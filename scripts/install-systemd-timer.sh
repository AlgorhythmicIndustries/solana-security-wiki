#!/usr/bin/env bash
# Install user systemd timer for incident-watcher on this machine.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
mkdir -p "$UNIT_DIR"

sed "s|@REPO_ROOT@|$ROOT|g" "$ROOT/scripts/systemd/incident-watcher.service" \
  >"$UNIT_DIR/incident-watcher.service"
cp "$ROOT/scripts/systemd/incident-watcher.timer" "$UNIT_DIR/incident-watcher.timer"

chmod +x "$ROOT/scripts/run-local.sh" "$ROOT/scripts/publish-if-changed.sh"

systemctl --user daemon-reload
systemctl --user enable --now incident-watcher.timer

echo "Installed user units in $UNIT_DIR"
echo ""
echo "  Next run:  $(systemctl --user list-timers incident-watcher.timer --no-pager | tail -1 || true)"
echo "  Run now:   systemctl --user start incident-watcher.service"
echo "  Logs:      journalctl --user -u incident-watcher.service -n 100 --no-pager"
echo "  Report:    $ROOT/scripts/output/run_report.txt"
echo "  Output:    $ROOT/scripts/output/  and  $ROOT/scripts/logs/"
echo ""
if ! loginctl show-user "$(whoami)" -p Linger 2>/dev/null | grep -q 'Linger=yes'; then
  echo "Tip: timers run without a login session if you enable linger:"
  echo "  sudo loginctl enable-linger $(whoami)"
fi
