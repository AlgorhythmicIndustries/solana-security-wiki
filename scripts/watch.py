"""Main entry point: runs the daily incident-watching pipeline.

Pipeline:
  1. Load existing incidents.json and seen_urls.json cache
  2. Fetch candidates from RSS, scrape, and search
  3. Triage with Claude — drop irrelevant/duplicates
  4. Cluster surviving articles by incident
  5. Extract structured records with Claude
  6. Merge into incidents.json (sorted by date desc)
  7. Update seen_urls.json with everything we processed
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

import anthropic

from fetcher import fetch_all
from extractor import triage_candidates, extract_incidents
from report import RunReport

# Resolve repo root from this script's location: scripts/watch.py → repo/
REPO_ROOT = Path(__file__).resolve().parent.parent
INCIDENTS_PATH = REPO_ROOT / "src" / "data" / "incidents.json"
SEEN_URLS_PATH = REPO_ROOT / "scripts" / "seen_urls.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
LOG_DIR = Path(__file__).resolve().parent / "logs"


def setup_logging() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_incidents() -> List[Dict[str, Any]]:
    if not INCIDENTS_PATH.exists():
        logging.warning("%s does not exist; starting from empty list", INCIDENTS_PATH)
        return []
    with INCIDENTS_PATH.open() as f:
        data = json.load(f)
    # Support both top-level array and {"incidents": [...]} structure;
    # adjust if your schema differs
    if isinstance(data, dict) and "incidents" in data:
        return data["incidents"]
    return data


def save_incidents(incidents: List[Dict[str, Any]], original_was_wrapped: bool) -> None:
    INCIDENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Sort by date desc, with stable secondary sort by id for determinism
    incidents.sort(
        key=lambda x: (x.get("date", ""), x.get("id", "")),
        reverse=True,
    )
    payload: Any = {"incidents": incidents} if original_was_wrapped else incidents
    with INCIDENTS_PATH.open("w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    logging.info("Wrote %d incidents to %s", len(incidents), INCIDENTS_PATH)


def load_seen_urls() -> Set[str]:
    if not SEEN_URLS_PATH.exists():
        return set()
    with SEEN_URLS_PATH.open() as f:
        data = json.load(f)
    return set(data.get("urls", []))


def save_seen_urls(seen: Set[str]) -> None:
    SEEN_URLS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SEEN_URLS_PATH.open("w") as f:
        json.dump(
            {"urls": sorted(seen), "updated_at": datetime.now(timezone.utc).isoformat()},
            f,
            indent=2,
        )
        f.write("\n")


def merge_incident(
    new_record: Dict[str, Any],
    existing: List[Dict[str, Any]],
    report: RunReport | None = None,
) -> bool:
    """Add new_record to existing if not a duplicate.

    Dedup keys:
      - `id` exact match (primary)
      - (normalized title prefix, date) — catches the case where Claude picked
        a different `id` for the same underlying incident

    Returns True if added, False if skipped as duplicate.
    """
    new_id = new_record.get("id")
    new_title = (new_record.get("title") or "").lower().strip()
    new_date = new_record.get("date")

    # Take the first 4 words of the title as a fuzzy match key — protocol name
    # typically appears at the start, so "Drift Protocol multisig / durable nonce
    # exploit" and "Drift Protocol exploit" would both share the prefix.
    new_title_key = " ".join(new_title.split()[:4])

    title = new_record.get("title") or new_id or "(untitled)"
    for inc in existing:
        if new_id and inc.get("id") == new_id:
            logging.info("Duplicate by id (%s); skipping", new_id)
            if report:
                report.record_merge(new_id, title, "duplicate", "same id")
            return False
        existing_title = (inc.get("title") or "").lower().strip()
        existing_title_key = " ".join(existing_title.split()[:4])
        if (
            new_title_key
            and existing_title_key == new_title_key
            and inc.get("date") == new_date
        ):
            logging.info(
                "Duplicate by (title prefix, date) (%s, %s); skipping",
                new_title_key, new_date,
            )
            if report:
                report.record_merge(
                    new_id or "?", title, "duplicate",
                    f"title prefix + date ({new_title_key}, {new_date})",
                )
            return False

    # Strip internal fields (those starting with _) before persisting
    clean = {k: v for k, v in new_record.items() if not k.startswith("_")}
    existing.append(clean)
    if report and new_id:
        report.record_merge(new_id, title, "added")
    return True


def main() -> int:
    setup_logging()
    OUTPUT_DIR.mkdir(exist_ok=True)
    report = RunReport()
    added = 0
    incidents_before = (
        INCIDENTS_PATH.read_text() if INCIDENTS_PATH.exists() else ""
    )

    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logging.error("ANTHROPIC_API_KEY not set")
            return 1

        client = anthropic.Anthropic(api_key=api_key)

        # Load state
        existing = load_incidents()
        # Detect whether incidents.json wraps the array in an object
        raw = json.loads(INCIDENTS_PATH.read_text()) if INCIDENTS_PATH.exists() else []
        original_was_wrapped = isinstance(raw, dict) and "incidents" in raw
        seen_urls = load_seen_urls()
        logging.info("Loaded %d existing incidents and %d seen URLs",
                     len(existing), len(seen_urls))

        # Stage 1: fetch
        candidates = fetch_all()
        report.set_fetch(candidates)
        if not candidates:
            logging.info("No candidates fetched; nothing to do")
            save_seen_urls(seen_urls)  # touch to update timestamp
            return 0

        # Save raw candidates for debugging
        with (OUTPUT_DIR / "candidates.json").open("w") as f:
            json.dump(candidates, f, indent=2, default=str)

        # Stage 2: triage
        survivors = triage_candidates(
            client, candidates, existing, seen_urls, report=report,
        )

        # Mark all candidates as seen so we don't re-triage them tomorrow
        for c in candidates:
            if c.get("url"):
                seen_urls.add(c["url"])

        if not survivors:
            logging.info("No survivors after triage")
            save_seen_urls(seen_urls)
            return 0

        with (OUTPUT_DIR / "triage_survivors.json").open("w") as f:
            json.dump(survivors, f, indent=2, default=str)

        # Stage 3: extract
        new_incidents = extract_incidents(
            client, survivors, existing, report=report,
        )

        with (OUTPUT_DIR / "extracted_incidents.json").open("w") as f:
            json.dump(new_incidents, f, indent=2, default=str)

        # Stage 4: merge & write
        for rec in new_incidents:
            if merge_incident(rec, existing, report=report):
                added += 1

        if added > 0:
            save_incidents(existing, original_was_wrapped)
            logging.info("Added %d new incidents", added)
        else:
            logging.info("No new incidents to add (all were duplicates)")

        save_seen_urls(seen_urls)
        return 0
    finally:
        incidents_after = (
            INCIDENTS_PATH.read_text() if INCIDENTS_PATH.exists() else ""
        )
        report.finalize(
            incidents_added=added,
            incidents_json_changed=incidents_before != incidents_after,
        )
        report_path = report.write(OUTPUT_DIR)
        logging.info("Run report: %s (JSON: %s)", report_path, OUTPUT_DIR / "run_report.json")


if __name__ == "__main__":
    sys.exit(main())
