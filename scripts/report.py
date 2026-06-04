"""Structured run report for incident-watcher (JSON + human-readable text)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _candidate_ref(cand: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "url": cand.get("url", ""),
        "title": cand.get("title", ""),
        "source_name": cand.get("source_name", ""),
        "source_tier": cand.get("source_tier"),
        "published_date": cand.get("published_date"),
    }


class RunReport:
    """Accumulates per-URL decisions across a single watch.py run."""

    def __init__(self) -> None:
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.finished_at: Optional[str] = None
        self.fetch: Dict[str, Any] = {"candidate_count": 0, "by_source": {}}
        self.already_seen: List[Dict[str, Any]] = []
        self.triage: List[Dict[str, Any]] = []
        self.extraction: List[Dict[str, Any]] = []
        self.merge: List[Dict[str, Any]] = []
        self.outcome: Dict[str, Any] = {}

    def set_fetch(self, candidates: List[Dict[str, Any]]) -> None:
        self.fetch["candidate_count"] = len(candidates)
        by_source: Dict[str, int] = {}
        for c in candidates:
            name = c.get("source_name") or "unknown"
            by_source[name] = by_source.get(name, 0) + 1
        self.fetch["by_source"] = by_source

    def record_already_seen(self, cand: Dict[str, Any]) -> None:
        self.already_seen.append(_candidate_ref(cand))

    def record_triage(
        self,
        cand: Dict[str, Any],
        verdict: str,
        reason: str = "",
        error: Optional[str] = None,
    ) -> None:
        row = {**_candidate_ref(cand), "verdict": verdict, "reason": reason}
        if error:
            row["error"] = error
        self.triage.append(row)

    def record_extraction(
        self,
        cluster: List[Dict[str, Any]],
        verdict: str,
        *,
        incident_id: Optional[str] = None,
        title: Optional[str] = None,
        reason: str = "",
        error: Optional[str] = None,
    ) -> None:
        row: Dict[str, Any] = {
            "verdict": verdict,
            "urls": [c.get("url", "") for c in cluster],
            "articles": [_candidate_ref(c) for c in cluster],
            "reason": reason,
        }
        if incident_id:
            row["incident_id"] = incident_id
        if title:
            row["title"] = title
        if error:
            row["error"] = error
        self.extraction.append(row)

    def record_merge(
        self,
        incident_id: str,
        title: str,
        action: str,
        detail: str = "",
    ) -> None:
        self.merge.append({
            "incident_id": incident_id,
            "title": title,
            "action": action,
            "detail": detail,
        })

    def finalize(
        self,
        *,
        incidents_added: int,
        incidents_json_changed: bool,
    ) -> None:
        self.finished_at = datetime.now(timezone.utc).isoformat()
        triage_include = sum(1 for t in self.triage if t.get("verdict") == "include")
        triage_skip = sum(1 for t in self.triage if t.get("verdict") == "skip")
        triage_error = sum(1 for t in self.triage if t.get("verdict") == "error")
        self.outcome = {
            "incidents_added": incidents_added,
            "incidents_json_changed": incidents_json_changed,
            "triage_evaluated": len(self.triage),
            "triage_include": triage_include,
            "triage_skip": triage_skip,
            "triage_error": triage_error,
            "already_seen_skipped": len(self.already_seen),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "fetch": self.fetch,
            "already_seen": self.already_seen,
            "triage": self.triage,
            "extraction": self.extraction,
            "merge": self.merge,
            "outcome": self.outcome,
        }

    def to_text(self) -> str:
        lines: List[str] = []
        lines.append("=" * 72)
        lines.append("INCIDENT WATCHER RUN REPORT")
        lines.append(f"Started:  {self.started_at}")
        if self.finished_at:
            lines.append(f"Finished: {self.finished_at}")
        lines.append("=" * 72)

        lines.append("")
        lines.append("## Fetch (keyword pre-filter)")
        lines.append(f"Candidates passed to triage pool: {self.fetch.get('candidate_count', 0)}")
        for name, count in sorted(
            (self.fetch.get("by_source") or {}).items(),
            key=lambda x: (-x[1], x[0]),
        ):
            lines.append(f"  - {name}: {count}")

        if self.already_seen:
            lines.append("")
            lines.append(f"## Already seen ({len(self.already_seen)}) — not sent to Claude triage")
            for row in self.already_seen:
                lines.append(f"  {row['url']}")
                lines.append(f"    {row.get('title', '')} ({row.get('source_name', '')})")

        lines.append("")
        lines.append(f"## Triage ({len(self.triage)} evaluated by Claude)")
        for row in self.triage:
            v = (row.get("verdict") or "?").upper()
            lines.append(f"  [{v}] {row.get('url', '')}")
            lines.append(f"       {row.get('title', '')}")
            lines.append(f"       Source: {row.get('source_name', '')} (tier {row.get('source_tier')})")
            if row.get("reason"):
                lines.append(f"       Reason: {row['reason']}")
            if row.get("error"):
                lines.append(f"       Error: {row['error']}")

        if self.extraction:
            lines.append("")
            lines.append(f"## Extraction ({len(self.extraction)} clusters)")
            for row in self.extraction:
                v = (row.get("verdict") or "?").upper()
                urls = row.get("urls") or []
                lines.append(f"  [{v}] cluster ({len(urls)} article(s))")
                for u in urls:
                    lines.append(f"       {u}")
                if row.get("incident_id"):
                    lines.append(f"       → id: {row['incident_id']}")
                if row.get("title"):
                    lines.append(f"       → title: {row['title']}")
                if row.get("reason"):
                    lines.append(f"       Reason: {row['reason']}")
                if row.get("error"):
                    lines.append(f"       Error: {row['error']}")

        if self.merge:
            lines.append("")
            lines.append("## Merge into incidents.json")
            for row in self.merge:
                lines.append(
                    f"  [{row.get('action', '').upper()}] {row.get('incident_id', '')}: "
                    f"{row.get('title', '')}"
                )
                if row.get("detail"):
                    lines.append(f"       {row['detail']}")

        if self.outcome:
            lines.append("")
            lines.append("## Outcome")
            o = self.outcome
            lines.append(f"  Triage: {o.get('triage_include', 0)} include, "
                         f"{o.get('triage_skip', 0)} skip, "
                         f"{o.get('triage_error', 0)} error")
            lines.append(f"  Already seen (skipped triage): {o.get('already_seen_skipped', 0)}")
            lines.append(f"  New incidents added: {o.get('incidents_added', 0)}")
            lines.append(f"  incidents.json changed: {o.get('incidents_json_changed', False)}")

        lines.append("")
        lines.append("Full machine-readable detail: scripts/output/run_report.json")
        lines.append("")
        return "\n".join(lines)

    def write(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        archived = output_dir / f"run_report-{stamp}.json"
        latest_json = output_dir / "run_report.json"
        latest_txt = output_dir / "run_report.txt"

        payload = self.to_dict()
        text = self.to_text()

        for path in (archived, latest_json):
            with path.open("w") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.write("\n")

        with latest_txt.open("w") as f:
            f.write(text)

        return latest_txt
