"""Google sign-in: loads, refreshes and saves the token."""

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import SCOPES, credentials_path, token_path


class CredentialsMissingError(FileNotFoundError):
    """credentials.json is missing (see README, "Set up Google access")."""


def _load_token():
    path = token_path()
    if not path.exists():
        return None
    try:
        return Credentials.from_authorized_user_file(str(path), SCOPES)
    except ValueError:
        # Corrupt or incomplete token file -> sign in again
        return None


def _save_token(creds):
    path = token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json())
    path.chmod(0o600)  # the token grants access to the calendar


def _login():
    secrets = credentials_path()
    if not secrets.exists():
        raise CredentialsMissingError(
            f"credentials.json not found: {secrets}")
    flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
    return flow.run_local_server(port=0)  # opens the browser


def get_service():
    """Return a Google Calendar client (signs in again if necessary)."""
    creds = _load_token()

    if creds and not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
        except RefreshError:
            # Token expired or revoked (e.g. testing mode after 7 days)
            creds = None

    if not creds or not creds.valid:
        creds = _login()
        _save_token(creds)

    return build("calendar", "v3", credentials=creds, cache_discovery=False)
