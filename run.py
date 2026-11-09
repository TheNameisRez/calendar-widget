#!/usr/bin/env python3
"""Start script: python3 run.py  (same as python -m calendar_widget).

If a virtual environment exists in ./venv (created by scripts/setup.sh), this
script switches to its Python automatically, so it also works when started
with the system Python.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / "venv"
VENV_PYTHON = VENV / "bin" / "python"

if VENV_PYTHON.exists() and Path(sys.prefix).resolve() != VENV.resolve():
    try:
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])
    except OSError:
        pass  # broken venv (e.g. folder was moved) -> try the current Python

from calendar_widget.__main__ import main

if __name__ == "__main__":
    main()
