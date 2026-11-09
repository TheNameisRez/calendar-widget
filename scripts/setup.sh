#!/usr/bin/env bash
# First-time setup for the calendar widget:
#   1. installs missing system packages (Debian/Ubuntu, asks for sudo)
#   2. creates the virtual environment in ./venv
#   3. installs the Python packages from requirements.txt
#   4. checks that everything can be imported
#   5. optionally sets up autostart
#
# Usage:  scripts/setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> 1/4 System packages"
if command -v apt-get >/dev/null 2>&1; then
  missing=()
  for pkg in python3-venv python3-gi gir1.2-gtk-3.0; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
      missing+=("$pkg")
    fi
  done
  if ((${#missing[@]})); then
    echo "Installing: ${missing[*]} (sudo password required)"
    sudo apt-get update
    sudo apt-get install -y "${missing[@]}"
  else
    echo "Already installed."
  fi
else
  echo "apt-get not found. Please install the equivalents of python3-venv,"
  echo "python3-gi (PyGObject) and GTK 3 with your package manager."
  echo "Package names for other distributions are listed in the README."
fi

echo "==> 2/4 Virtual environment"
if [[ -x venv/bin/python ]]; then
  echo "venv already exists."
else
  # PyGObject (python3-gi) is built for the system Python, so use that one
  # even if another Python (conda, pyenv, ...) comes first in PATH.
  # --system-site-packages makes the system packages visible in the venv.
  if [[ -x /usr/bin/python3 ]]; then
    SYSTEM_PYTHON=/usr/bin/python3
  else
    SYSTEM_PYTHON=python3
  fi
  "$SYSTEM_PYTHON" -m venv --system-site-packages venv
fi

echo "==> 3/4 Python packages"
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt

echo "==> 4/4 Check"
if ! check_output="$(./venv/bin/python -c "import gi, google.auth, googleapiclient, google_auth_oauthlib" 2>&1)"; then
  echo "Error: a required module cannot be imported:" >&2
  echo "  $(echo "$check_output" | tail -n 1)" >&2
  echo "If 'gi' is the problem, delete the venv folder and run this script again." >&2
  exit 1
fi
echo "All modules found."

CREDENTIALS="$(./venv/bin/python -c 'from calendar_widget.config import credentials_path; print(credentials_path())')"
echo
if [[ -f "$CREDENTIALS" ]]; then
  echo "Google credentials found: $CREDENTIALS"
else
  echo "One step is still missing: the Google credentials."
  echo "Create them as described in the README (\"Set up Google access\") and save the file as:"
  echo "  $CREDENTIALS"
fi

if [[ -t 0 ]]; then
  echo
  read -r -p "Start the widget automatically at login? [y/N] " answer
  if [[ "$answer" =~ ^[Yy]$ ]]; then
    "$ROOT/scripts/install-autostart.sh"
  fi
fi

echo
echo "Setup finished. Start the widget with:"
echo "  python3 $ROOT/run.py"
