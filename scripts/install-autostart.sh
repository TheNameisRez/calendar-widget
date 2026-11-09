#!/usr/bin/env bash
# Creates an autostart entry for the calendar widget.
#
# Usage:  scripts/install-autostart.sh [--x11]
#   --x11  forces X11 mode (GDK_BACKEND=x11), useful on Wayland when the
#          window position or "keep below" is ignored.
#
# To remove:  rm ~/.config/autostart/calendar-widget.desktop
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/venv/bin/python"
TARGET_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
TARGET="$TARGET_DIR/calendar-widget.desktop"

ENV_PREFIX=""
if [[ "${1:-}" == "--x11" ]]; then
  ENV_PREFIX="env GDK_BACKEND=x11 "
fi

if [[ ! -x "$PYTHON" ]]; then
  echo "Error: $PYTHON not found." >&2
  echo "Create the virtual environment first (see README, Installation)." >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"
cat > "$TARGET" <<EOF
[Desktop Entry]
Type=Application
Name=Calendar Widget
Comment=5-day overview of your Google Calendar
Exec=${ENV_PREFIX}"${PYTHON}" "${ROOT}/run.py"
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=5
Terminal=false
EOF

echo "Autostart entry created: $TARGET"
echo "It takes effect at your next login."
