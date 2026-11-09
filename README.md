# Calendar Widget

A narrow desktop widget for Linux that starts at login and shows the next five
days from your Google Calendar. The **+** button creates new events, which are
written straight to Google Calendar.

Tested on Ubuntu 24.04 (GNOME). Windows and macOS are not supported
(see [Compatibility](#compatibility)).

## Features

- 5-day overview, about one fifth of the screen width, on the right edge
- Shows events from **all** calendars of the Google account
- Create new events (title, date, time or all-day) in the primary calendar
- Refreshes automatically every 5 minutes
- Autostart at login
- Weekday and month names follow the system language

## Requirements

- Linux with GTK 3 and Python 3.10 or newer (Ubuntu 24.04 ships Python 3.12)
- A Google account and your own Google Cloud project (free, see below)

## Installation

```bash
git clone https://github.com/<your-name>/calendar-widget.git
cd calendar-widget
./scripts/setup.sh
```

The setup script installs the missing system packages (Debian/Ubuntu, asks for
your sudo password), creates the virtual environment in `venv/`, installs the
Python packages, checks that everything can be imported and offers to set up
autostart.

<details>
<summary>Manual installation</summary>

```bash
sudo apt update
sudo apt install -y python3-venv python3-gi gir1.2-gtk-3.0

# --system-site-packages is needed so that PyGObject (python3-gi) is visible
python3 -m venv --system-site-packages venv
./venv/bin/pip install -r requirements.txt
```

</details>

### Set up Google access (one time)

Every user needs their own API access. The credentials must never go into the
repository.

1. Create a new project in the [Google Cloud Console](https://console.cloud.google.com).
2. Under "APIs & Services" → "Library", enable the **Google Calendar API**.
3. Set up the OAuth consent screen (in newer versions of the console:
   "Google Auth Platform"): user type "External", any app name.
4. Under "Audience", add your own Google address as a **test user**.
   Without this entry Google answers with error 403.
5. Under "Credentials", create an **OAuth client ID** of type **Desktop app**
   and download the JSON file.
6. Save the file as `credentials.json`:

   ```bash
   mkdir -p ~/.config/calendar-widget
   mv ~/Downloads/client_secret_*.json ~/.config/calendar-widget/credentials.json
   ```

On first start a browser window opens for the login. Afterwards a token is
stored as `token.json` in the same folder.

> **Note on testing mode:** While the app has the status "Testing", the token
> expires after 7 days and you are asked to sign in again. For personal use you
> can set the app to "In production" under "Audience". No verification is
> needed for that, Google only shows an "unverified app" warning at login.

## Run

```bash
python3 run.py
```

`run.py` automatically switches to the Python of the `venv` folder if it
exists, so it does not matter which Python you start it with. Equivalent:
`./venv/bin/python -m calendar_widget`.

## Autostart

With the included script (creates `~/.config/autostart/calendar-widget.desktop`
with the correct paths):

```bash
./scripts/install-autostart.sh
```

On Wayland, GNOME sometimes ignores the window position and "keep below".
In that case use X11 mode:

```bash
./scripts/install-autostart.sh --x11
```

To remove it: `rm ~/.config/autostart/calendar-widget.desktop`.

Alternatively, add an entry in the Ubuntu "Startup Applications" app. As the
command, enter the full path to the virtual environment's Python, followed by
the path to `run.py`, both without `~`.

## Configuration

Settings are in [`calendar_widget/config.py`](calendar_widget/config.py):

| Setting | Meaning | Default |
|---|---|---|
| `DAYS` | Number of days shown | 5 |
| `REFRESH_MINUTES` | Refresh interval | 5 |
| `WIDTH_FRACTION` | Width relative to the screen | 0.2 |

Appearance (colors, font sizes): [`calendar_widget/ui/style.css`](calendar_widget/ui/style.css).

Where `credentials.json` and `token.json` are looked up:

1. The folder in the environment variable `CALENDAR_WIDGET_DIR`
2. `~/.config/calendar-widget/`
3. The project folder (only if a `credentials.json` already lies there, for users of the first version)

## Project structure

```text
calendar-widget/
├── run.py                      Start script (thin launcher)
├── calendar_widget/
│   ├── __main__.py             Entry point (python -m calendar_widget)
│   ├── config.py               Settings and file paths
│   ├── models.py               Dataclasses Event and NewEvent
│   ├── auth.py                 Google login, load/refresh/save token
│   ├── calendar_api.py         Fetch and create events
│   ├── agenda.py               Group events by day
│   └── ui/
│       ├── main_window.py      Main window (GTK 3)
│       ├── new_event_dialog.py "New event" dialog
│       └── style.css           Appearance
├── scripts/
│   ├── setup.sh                First-time setup (packages, venv, checks)
│   └── install-autostart.sh    Create the autostart entry
├── tests/
│   └── test_core.py            Tests for the GUI-free logic
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

The logic (`auth`, `calendar_api`, `agenda`, `models`) is separated from the
user interface (`ui/`). This makes it possible to replace the interface later
without touching the rest.

## Compatibility

| System | Status |
|---|---|
| Ubuntu 24.04 (GNOME) | tested |
| Other Linux desktops (KDE, XFCE, Cinnamon) | should work, autostart via `.desktop` files is a standard there as well |
| Other distributions | package names differ, e.g. `python3-gobject` and `gtk3` on Fedora |
| Linux with Wayland | limited: position and "keep below" may be ignored, `--x11` helps |
| Windows, macOS | not supported: GTK 3 via PyGObject and the window hints are Linux-specific, and autostart works differently there |

A version for other systems would mean rebuilding the interface on a
cross-platform toolkit such as Qt (PySide6).

## Security

- Never commit or share `credentials.json` and `token.json`. Both are listed in
  `.gitignore`.
- `token.json` grants read and write access to your Google Calendar. The
  program creates the file with permissions 600.
- To revoke access, go to [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
  and delete `token.json` afterwards.

## Development

Run the tests (no Google access and no GTK needed):

```bash
python3 -m unittest
```

## Troubleshooting

- **"Missing Python module 'google'" (or 'gi'):** The setup has not been run
  yet, or the `venv` folder is outdated (for example after moving the project).
  Delete `venv/` and run `./scripts/setup.sh` again.
- **Error 403 / "Access blocked":** Your Google address is not listed as a test
  user (step 4 above).
- **"credentials.json not found":** Put the file in the right place, see
  [Configuration](#configuration).
- **Creating an event fails with 403:** The token comes from an older
  read-only version. Delete `token.json` and sign in again.
- **Widget is not on the edge or covers other windows:** Set up autostart with
  `--x11`, or choose "Ubuntu on Xorg" at the login screen.

## Roadmap

- Edit and delete events
- Load in the background so the interface does not freeze briefly while refreshing
- Calendar selection and showing multi-day events on every day they cover
- Translatable interface texts
- Packaging (`pyproject.toml`)

## License

[MIT](LICENSE)
