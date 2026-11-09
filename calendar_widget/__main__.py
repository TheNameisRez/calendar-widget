"""Entry point: python -m calendar_widget"""

import sys

# Third-party modules that come from requirements.txt or the system packages.
_EXTERNAL_MODULES = {"gi", "google", "google_auth_oauthlib", "googleapiclient"}


def main():
    # Imported here so that the rest of the package stays importable without
    # GTK (e.g. for the tests).
    try:
        from .ui.main_window import run
    except ModuleNotFoundError as ex:
        if (ex.name or "").split(".")[0] not in _EXTERNAL_MODULES:
            raise
        sys.exit(
            f"Missing Python module '{ex.name}'.\n"
            "Run scripts/setup.sh once to install everything "
            "(see README, Installation)."
        )

    run()


if __name__ == "__main__":
    main()
