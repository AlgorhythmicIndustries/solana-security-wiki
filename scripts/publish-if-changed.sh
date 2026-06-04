#!/usr/bin/env bash
# If incidents.json changed, commit, push, and open/update a PR (requires gh auth + git push).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

INCIDENTS="src/data/incidents.json"
BRANCH="incident-watcher/auto-update"

if git diff --quiet HEAD -- "$INCIDENTS"; then
  echo "No changes to $INCIDENTS — skipping publish."
  exit 0
fi

git add -- "$INCIDENTS"

git checkout -B "$BRANCH"
git commit -m "$(cat <<'EOF'
chore: add new Solana security incident(s)
EOF
)"

git push -u origin "$BRANCH"

PR_BODY="$(cat <<'EOF'
Automated incident detection found new entries.

**Please review carefully before merging:**
- Verify the loss amount and date against primary sources
- Confirm the incident is actually Solana-related (not just mentioned alongside Solana)
- Check that sources are reachable and authoritative
- Ensure no duplicates with existing entries

See `scripts/output/run_report.txt` on the runner for triage decisions and source URLs.
EOF
)"

if gh pr list --head "$BRANCH" --state open --json number -q '.[0].number' 2>/dev/null | grep -q .; then
  echo "Open PR already exists on $BRANCH — push updated the branch."
  gh pr view --head "$BRANCH" --web 2>/dev/null || gh pr view --head "$BRANCH"
else
  gh pr create \
    --base "$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)" \
    --head "$BRANCH" \
    --title "🚨 New Solana security incident(s) detected" \
    --body "$PR_BODY" \
    --label "automated" \
    --label "security-incident" \
    --label "needs-review" 2>/dev/null || \
  gh pr create \
    --head "$BRANCH" \
    --title "🚨 New Solana security incident(s) detected" \
    --body "$PR_BODY"
fi
