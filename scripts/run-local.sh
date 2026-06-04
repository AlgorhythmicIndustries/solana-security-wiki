#!/usr/bin/env bash
# Run the incident watcher from a repo-local venv. Used by cron/systemd or by hand.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VENV="$ROOT/scripts/.venv"
if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --upgrade pip
  "$VENV/bin/pip" install -r "$ROOT/scripts/requirements.txt"
fi

if [[ -f "$ROOT/scripts/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT/scripts/.env"
  set +a
else
  echo "Missing $ROOT/scripts/.env — copy scripts/.env.example and add API keys." >&2
  exit 1
fi

"$VENV/bin/python" "$ROOT/scripts/watch.py"

# Optional: commit + push + PR when incidents.json changes (needs gh auth login).
if [[ "${INCIDENT_WATCHER_PUBLISH:-0}" == "1" ]]; then
  "$ROOT/scripts/publish-if-changed.sh"
fi
