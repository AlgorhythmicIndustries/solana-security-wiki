"""Extractor: uses Claude to filter candidates and emit structured incidents.

Two-stage pipeline:
  1. Triage: for each candidate, ask Claude "is this a real, new Solana
     security incident not already in our database?" — short yes/no with reason.
  2. Extraction: for candidates that pass triage, fetch the full article and
     ask Claude to emit a structured incident record matching incidents.json schema.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from report import RunReport

import anthropic
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

MODEL = "claude-opus-4-8"
USER_AGENT = "incident-watcher/1.0"

# Schema for each incident record. Matches the existing incidents.json structure
# in the wiki repo. The prompt below explicitly enumerates every field.
INCIDENT_SCHEMA_DESCRIPTION = """
Every incident record must have these fields, in this order:

  "id"                — slug, lowercase, kebab-case, includes month and year.
                        Examples: "drift-protocol-apr-2026", "loopscale-apr-2025",
                        "swissborg-kiln-sep-2025". Should be unique across the file.

  "title"             — short human-readable title naming the target and the
                        attack class. Examples: "Drift Protocol multisig / durable
                        nonce exploit", "Loopscale RateX collateral oracle exploit".
                        Roughly 4-10 words.

  "date"              — ISO date YYYY-MM-DD of when the incident OCCURRED (the
                        attack execution date), not when it was reported.

  "category"          — one of: "application", "supply_chain", "wallet",
                        "exchange", "social_engineering", "phishing", "rug_pull",
                        "account_compromise", "network", "infrastructure".
                        Use "application" for smart-contract / on-chain logic
                        exploits. Use "supply_chain" for compromises of dependencies,
                        APIs, or third-party infrastructure (Kiln-style, npm
                        packages). Use "social_engineering" only when the *primary*
                        vector was tricking humans (Drift-style operations).

  "severity"          — one of: "low", "medium", "high", "critical". Rough guide:
                        - critical: $50M+, ecosystem-wide implications, or novel
                          vector creating contagion risk
                        - high: $5M-$50M, single-protocol impact
                        - medium: $500K-$5M
                        - low: under $500K, or no direct financial loss
                          (account compromises with no funds drained)

  "estimatedLossUsd"  — integer USD. Use the most widely-cited figure across
                        Tier 1/2 sources. Use 0 if no funds were lost (e.g.
                        account compromise that didn't lead to drains). Use null
                        only if the incident clearly involved losses but no
                        figure is yet public.

  "lossDescription"   — 1-2 sentence prose qualifier on the loss number: who
                        bore the loss, what was recovered, how funds moved.
                        Example: "Largest Solana DeFi loss of 2026 in public
                        reporting; laundering via swaps, bridges, mixers."

  "summary"           — 2-4 sentence neutral summary of what happened, the
                        mechanism, and any attribution. Should read like a wiki
                        lead paragraph.

  "details"           — 1-3 sentences of additional technical or operational
                        context that didn't fit in summary. Often emphasizes
                        what was NOT the cause (e.g. "Post-mortems emphasize
                        operational security and multisig ceremony design rather
                        than a single on-chain logic bug.")

  "tags"              — array of 3-8 lowercase kebab-case tags. Mix of:
                        protocol name(s), attack vector, asset class, and notable
                        features. Examples for Drift: ["drift", "durable-nonce",
                        "multisig", "social-engineering", "perps"].

  "relatedIds"        — array of `id`s of related incidents already in the
                        database. Empty array if none. Examples: a remediation
                        announcement might be related to the incident that
                        prompted it.

  "sources"           — array of {label, url} objects. EVERY source article
                        provided to you should appear here. The label should be
                        a short publication name with optional qualifier, e.g.
                        "TRM Labs", "CoinDesk — durable nonce", "Drift Protocol (X)".

  "lesson"            — 1-2 sentence takeaway suitable for a wiki "lesson"
                        callout. Should generalize beyond the specific incident.
                        Example: "Sophisticated DPRK-style social engineering
                        against contributors and multisig signers is now the
                        largest loss vector in DeFi; controls must include
                        human-process security, signer hygiene, and durable-nonce
                        awareness alongside smart-contract audits."

  "mitigations"       — array of 4-8 specific, actionable mitigations that
                        would have prevented or limited THIS incident. Each
                        should be a complete sentence. Be concrete and technical
                        — "improve security" is not a mitigation; "Mandatory
                        minimum timelock on Security Council changes (no
                        zero-timelock migrations) and on collateral whitelist
                        changes" is. Mix protocol-level controls and human-
                        process controls where both apply.
"""

# Canonical example record. Used as a few-shot exemplar in the extraction
# prompt so Claude matches the wiki's style precisely. Keep this in sync if
# the schema or stylistic conventions evolve.
CANONICAL_EXAMPLE = {
    "id": "drift-protocol-apr-2026",
    "title": "Drift Protocol multisig / durable nonce exploit",
    "date": "2026-04-01",
    "category": "application",
    "severity": "critical",
    "estimatedLossUsd": 285000000,
    "lossDescription": "Largest Solana DeFi loss of 2026 in public reporting; laundering via swaps, bridges, mixers.",
    "summary": "Long-running social engineering against contributors led to device/repo compromise, abuse of pre-signed durable-nonce txs and a zero-timelock council migration, then whitelisting of fake collateral (CVT) to borrow real assets. Widely attributed to DPRK-linked groups in industry reporting.",
    "details": "Post-mortems emphasize operational security and multisig ceremony design rather than a single on-chain logic bug.",
    "tags": ["drift", "durable-nonce", "multisig", "social-engineering", "perps"],
    "relatedIds": ["solana-foundation-stride-sirn-apr-2026"],
    "sources": [
        {"label": "Drift Protocol (X)", "url": "https://x.com/DriftProtocol"},
        {"label": "TRM Labs", "url": "https://www.trmlabs.com/resources/blog/north-korean-hackers-attack-drift-protocol-in-285-million-heist"},
        {"label": "Elliptic", "url": "https://www.elliptic.co/blog/drift-protocol-exploited-for-286-million-in-suspected-dprk-linked-attack"},
        {"label": "Chainalysis — lessons", "url": "https://www.chainalysis.com/blog/lessons-from-the-drift-hack/"},
        {"label": "CoinDesk — durable nonce", "url": "https://www.coindesk.com/tech/2026/04/02/how-a-solana-feature-designed-for-convenience-let-an-attacker-drain-usd270-million-from-drift"},
    ],
    "lesson": "Sophisticated DPRK-style social engineering against contributors and multisig signers is now the largest loss vector in DeFi; controls must include human-process security, signer hygiene, and durable-nonce awareness alongside smart-contract audits.",
    "mitigations": [
        "Treat any pre-signed transaction (including durable nonces) as a long-lived signed authorization; track which nonces are outstanding and restrict their reuse.",
        "Require human-readable decoding of every multisig payload and out-of-band confirmation between independent signers before approval.",
        "Mandatory minimum timelock on Security Council changes (no zero-timelock migrations) and on collateral whitelist changes.",
        "Strict allow-list for new collateral assets with multi-day cooling period and on-chain governance vote.",
        "Air-gap signing from internet-connected workstations; never click links or open attachments on a signing device.",
        "Endpoint-detection (EDR) and minimum-trust IDE/extension policies for all team members; treat repository clones from external counterparties as untrusted code.",
    ],
}

# Stable instructions reused on every call of a given stage (cached via `system` when enabled).
TRIAGE_SYSTEM = """You are screening news articles to identify NEW security incidents in the Solana blockchain ecosystem.

Decide for each candidate:
1. Is this article reporting a SECURITY INCIDENT (hack, exploit, drain, rug pull, phishing campaign, key compromise, supply chain attack)? Not just price commentary, regulatory news, or general security analysis.
2. Does the incident affect the SOLANA ecosystem (Solana-native protocol, Solana wallet, Solana-side of an exchange, Solana staking infra)? Mere mentions of Solana alongside other chains do not count.
3. Is this a NEW incident not already in the existing database? Re-coverage of an existing entry should be skipped.

Respond with ONLY a single JSON object, no other text:
{"verdict": "include" | "skip", "reason": "brief reason"}"""

_EXTRACTION_EXAMPLE_JSON = json.dumps(CANONICAL_EXAMPLE, indent=2, ensure_ascii=False)
EXTRACTION_SYSTEM = f"""You are extracting a structured security-incident record for a Solana ecosystem wiki, from one or more news articles about a single incident.

The wiki has a strict schema. Every record must conform to it exactly. Here is the field-by-field specification:
{INCIDENT_SCHEMA_DESCRIPTION}

Here is a canonical example record from the wiki, showing the exact style, level of technical detail, and tone you should match:
{_EXTRACTION_EXAMPLE_JSON}

Rules:
1. Output a single JSON object matching the schema. Same field order as the example. Use the exact same field NAMES (camelCase: `estimatedLossUsd`, `lossDescription`, `relatedIds`, NOT snake_case).
2. The `id` must be unique — check the existing list and choose something not already taken.
3. Every source URL provided in the user message must appear in the `sources` array. If multiple articles from the same publication exist, include them all (with disambiguating labels like "CoinDesk — initial report" and "CoinDesk — durable nonce").
4. The `summary` and `details` and `lesson` should be in the same neutral, technical, slightly dry voice as the example. Do not editorialize, speculate, or use marketing language.
5. The `mitigations` should be specific and actionable, in the same style as the example. Avoid generic advice.
6. If multiple sources cite different loss figures, pick the most-corroborated one for `estimatedLossUsd` and explain the variation in `lossDescription`.
7. The `category` and `severity` values must be EXACTLY one of the enumerated values from the schema description.

If after reading the articles you conclude this is NOT actually a Solana security incident (e.g. the articles are about a Sui or Ethereum protocol, or are general security commentary, or describe an incident that's already in the existing database), output exactly: {{"skip": true, "reason": "<brief reason>"}}

Output ONLY the JSON object. No prose, no markdown fences, no explanation."""

CLUSTER_SYSTEM = """These articles all describe Solana ecosystem security incidents. Group them by which articles describe the SAME underlying incident.

Output ONLY a JSON array of arrays, where each inner array contains the indices of articles describing the same incident.
Example: [[0, 2], [1], [3, 4, 5]]
Output only the JSON array, nothing else."""


def _prompt_cache_enabled() -> bool:
    """Opt out with ANTHROPIC_PROMPT_CACHE=0 in scripts/.env."""
    return os.environ.get("ANTHROPIC_PROMPT_CACHE", "1").strip().lower() not in (
        "0", "false", "no", "off",
    )


def _create_message(
    client: anthropic.Anthropic,
    *,
    max_tokens: int,
    system: Union[str, List[Dict[str, Any]]],
    user_content: str,
    stage: str,
) -> Any:
    """Messages API wrapper with optional ephemeral prompt caching.

    Static `system` text is identical across repeated calls in one run; only
    `user_content` changes. Top-level cache_control matches Anthropic's
    automatic caching pattern (see prompt caching docs).
    """
    kwargs: Dict[str, Any] = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_content}],
    }
    if _prompt_cache_enabled():
        kwargs["cache_control"] = {"type": "ephemeral"}
    resp = client.messages.create(**kwargs)
    _log_cache_usage(resp, stage)
    return resp


def _log_cache_usage(resp: Any, stage: str) -> None:
    usage = getattr(resp, "usage", None)
    if not usage:
        return
    read = getattr(usage, "cache_read_input_tokens", None) or 0
    created = getattr(usage, "cache_creation_input_tokens", None) or 0
    if read or created:
        log.info(
            "Prompt cache [%s]: read=%s tokens, created=%s tokens",
            stage, read, created,
        )


def _fetch_article_text(url: str, max_chars: int = 12000) -> Optional[str]:
    """Fetch and clean an article. Returns up to max_chars of body text."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Strip nav/footer/script/style for cleaner text
        for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        return text[:max_chars]
    except Exception as e:
        log.warning("Failed to fetch %s: %s", url, e)
        return None


def _existing_incident_summary(incidents: List[Dict[str, Any]]) -> str:
    """Compact summary of existing incidents for the dedup check.

    We don't want to send the full incidents.json on every triage call —
    just enough that Claude can recognize a duplicate. Format is one line per
    incident: `id | date | title | $loss`.
    """
    lines = []
    for inc in incidents:
        inc_id = inc.get("id", "?")
        title = inc.get("title", "?")
        date = inc.get("date", "?")
        loss = inc.get("estimatedLossUsd")
        if loss is None:
            loss_str = "n/a"
        elif loss == 0:
            loss_str = "$0"
        elif loss >= 1_000_000:
            loss_str = f"${loss/1e6:.1f}M"
        elif loss >= 1_000:
            loss_str = f"${loss/1e3:.0f}K"
        else:
            loss_str = f"${loss}"
        lines.append(f"- {inc_id} | {date} | {title} | {loss_str}")
    return "\n".join(lines) if lines else "(none)"


def triage_candidates(
    client: anthropic.Anthropic,
    candidates: List[Dict[str, Any]],
    existing_incidents: List[Dict[str, Any]],
    seen_urls: set,
    report: Optional["RunReport"] = None,
) -> List[Dict[str, Any]]:
    """Ask Claude which candidates are real new Solana incidents.

    Skips URLs we've already processed. Returns subset of candidates worth
    proceeding to extraction.
    """
    existing_summary = _existing_incident_summary(existing_incidents)
    fresh_candidates = []
    for c in candidates:
        if c["url"] in seen_urls:
            if report:
                report.record_already_seen(c)
        else:
            fresh_candidates.append(c)
    log.info("Triaging %d fresh candidates (skipping %d already seen)",
             len(fresh_candidates), len(candidates) - len(fresh_candidates))

    triage_system = (
        f"{TRIAGE_SYSTEM}\n\nExisting incidents already in our database:\n{existing_summary}"
    )
    survivors = []
    for cand in fresh_candidates:
        user_content = f"""Candidate article:
- Title: {cand['title']}
- URL: {cand['url']}
- Published: {cand['published_date']}
- Source: {cand['source_name']} (tier {cand['source_tier']})
- Snippet: {cand['snippet']}"""

        try:
            resp = _create_message(
                client,
                max_tokens=200,
                system=triage_system,
                user_content=user_content,
                stage="triage",
            )
            text = resp.content[0].text.strip()
            # Strip code fences if Claude added them
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            verdict = json.loads(text)
            reason = verdict.get("reason", "")
            if verdict.get("verdict") == "include":
                cand["_triage_reason"] = reason
                survivors.append(cand)
                if report:
                    report.record_triage(cand, "include", reason)
                log.info("INCLUDE: %s — %s — %s", cand["url"], cand["title"][:50], reason)
            else:
                if report:
                    report.record_triage(cand, "skip", reason)
                log.info("SKIP: %s — %s — %s", cand["url"], cand["title"][:50], reason)
        except Exception as e:
            log.error("Triage failed for %s: %s", cand["url"], e)
            if report:
                report.record_triage(cand, "error", error=str(e))
            # Be conservative: failed triage → skip, don't pollute the PR with garbage
            continue

        # Be polite to the API
        time.sleep(0.5)

    log.info("Triage complete: %d candidates survived", len(survivors))
    return survivors


def extract_incidents(
    client: anthropic.Anthropic,
    survivors: List[Dict[str, Any]],
    existing_incidents: List[Dict[str, Any]],
    report: Optional["RunReport"] = None,
) -> List[Dict[str, Any]]:
    """For each surviving candidate, fetch full article and extract structured record."""
    incidents_out = []

    # Group candidates by likely-same-incident before extraction so we get
    # one record per incident rather than one per news article. We do this
    # by asking Claude to cluster.
    if len(survivors) > 1:
        clusters = _cluster_survivors(client, survivors)
    else:
        clusters = [[s] for s in survivors]

    log.info("Extracting %d incident clusters from %d articles", len(clusters), len(survivors))

    existing_compact = _existing_incident_summary(existing_incidents)
    extraction_system = (
        f"{EXTRACTION_SYSTEM}\n\n"
        f"Existing incidents already in the database (for duplicate-checking and for `relatedIds`):\n"
        f"{existing_compact}"
    )

    for cluster in clusters:
        # Fetch article bodies for the whole cluster (each gives different angle)
        article_blocks = []
        for cand in cluster:
            # SlowMist entries have full text already; no need to re-fetch
            if cand.get("_slowmist_full_text"):
                body = cand["_slowmist_full_text"]
            else:
                body = _fetch_article_text(cand["url"])
            if not body:
                continue
            article_blocks.append(
                f"---\nSource: {cand['source_name']}\nURL: {cand['url']}\n"
                f"Title: {cand['title']}\nPublished: {cand['published_date']}\n\n{body}\n"
            )

        if not article_blocks:
            if report:
                report.record_extraction(
                    cluster, "no_body",
                    reason="Could not fetch article text for any URL in cluster",
                )
            continue

        joined_articles = "\n\n".join(article_blocks)
        # Truncate aggressively if too long — Claude has a big context window but
        # we don't want to burn tokens
        if len(joined_articles) > 40000:
            joined_articles = joined_articles[:40000] + "\n\n[truncated]"

        user_content = f"Source articles for the new incident you should extract:\n{joined_articles}"

        try:
            resp = _create_message(
                client,
                max_tokens=3000,
                system=extraction_system,
                user_content=user_content,
                stage="extraction",
            )
            text = resp.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            record = json.loads(text)
            if record.get("skip"):
                reason = record.get("reason", "")
                if report:
                    report.record_extraction(cluster, "declined", reason=reason)
                log.info("Extraction declined (%s): %s", cluster[0]["url"], reason)
                continue
            # Stash the candidate URLs for the seen-urls cache regardless of outcome
            record["_source_urls"] = [c["url"] for c in cluster]
            incidents_out.append(record)
            inc_id = record.get("id", "")
            title = record.get("title") or inc_id
            if report:
                report.record_extraction(
                    cluster, "extracted",
                    incident_id=inc_id, title=title,
                )
            log.info("Extracted: %s — %s ($%s)",
                     inc_id, title, record.get("estimatedLossUsd"))
        except Exception as e:
            log.error("Extraction failed for cluster (first url: %s): %s",
                      cluster[0]["url"], e)
            if report:
                report.record_extraction(cluster, "error", error=str(e))
            continue

        time.sleep(0.5)

    return incidents_out


def _cluster_survivors(
    client: anthropic.Anthropic,
    survivors: List[Dict[str, Any]],
) -> List[List[Dict[str, Any]]]:
    """Group articles that describe the same incident.

    Three Decrypt+CoinDesk+TheBlock articles about the same hack should produce
    ONE incident record, not three.
    """
    if len(survivors) <= 1:
        return [survivors]

    items_text = "\n".join(
        f"{i}. {c['title']} ({c['source_name']}, {c['published_date']})"
        for i, c in enumerate(survivors)
    )

    user_content = f"Articles:\n{items_text}"

    try:
        resp = _create_message(
            client,
            max_tokens=500,
            system=CLUSTER_SYSTEM,
            user_content=user_content,
            stage="cluster",
        )
        text = resp.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        groups = json.loads(text)
        return [[survivors[i] for i in group] for group in groups]
    except Exception as e:
        log.error("Clustering failed, treating each article as separate: %s", e)
        return [[s] for s in survivors]
