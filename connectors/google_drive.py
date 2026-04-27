import os
import json
import io

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload

from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    get_tokens_path,
    SCOPES,
    DOWNLOAD_DIR,
)


def get_flow() -> Flow:
    """Create and return a Google OAuth2 flow object."""
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": [GOOGLE_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    return flow


def get_auth_url() -> str:
    """Returns the Google OAuth consent screen URL."""
    flow = get_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code_for_tokens(code: str) -> dict:
    """Exchange the auth code for access + refresh tokens and save them."""
    flow = get_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else SCOPES,
    }
    with open(get_tokens_path(), "w") as f:
        json.dump(token_data, f)
    return token_data


def load_credentials() -> Credentials | None:
    """Load stored OAuth credentials. Refresh if expired."""
    if not os.path.exists(get_tokens_path()):
        return None
    with open(get_tokens_path(), "r") as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )

    # Refresh token if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        with open(get_tokens_path(), "w") as f:
            json.dump(token_data, f)

    return creds


def is_drive_connected() -> bool:
    """Check if valid Drive credentials exist."""
    return os.path.exists(get_tokens_path())


def get_user_email() -> str | None:
    """Fetch the connected user's email address."""
    creds = load_credentials()
    if not creds:
        return None
    try:
        service = build("oauth2", "v2", credentials=creds)
        user_info = service.userinfo().get().execute()
        return user_info.get("email")
    except Exception as e:
        return None


def get_drive_files(folder_id: str = None) -> list[dict]:
    """List all PDF and TXT files from the user's Drive or a specific folder."""
    creds = load_credentials()
    if not creds:
        raise ValueError("Not authenticated. Please visit /auth/login first.")

    service = build("drive", "v3", credentials=creds)

    query = (
        "mimeType='application/pdf' or "
        "mimeType='text/plain'"
    )
    
    if folder_id:
        query = f"({query}) and '{folder_id}' in parents"

    results = []
    page_token = None

    while True:
        response = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                pageToken=page_token,
            )
            .execute()
        )
        results.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return results


def download_file(file_id: str, file_name: str, mime_type: str) -> str:
    """
    Download a file from Drive to the local downloads/ directory.
    For Google Docs, export as plain text.
    Returns the local file path.
    """
    creds = load_credentials()
    service = build("drive", "v3", credentials=creds)

    # Sanitize filename
    safe_name = "".join(c for c in file_name if c.isalnum() or c in (" ", ".", "_", "-")).rstrip()
    local_path = os.path.join(DOWNLOAD_DIR, f"{file_id}_{safe_name}")

    if mime_type == "application/vnd.google-apps.document":
        # Export Google Doc as plain text
        local_path = local_path + ".txt"
        request = service.files().export_media(fileId=file_id, mimeType="text/plain")
    elif mime_type == "application/pdf":
        local_path = local_path + ".pdf" if not local_path.endswith(".pdf") else local_path
        request = service.files().get_media(fileId=file_id)
    else:
        # text/plain
        local_path = local_path + ".txt" if not local_path.endswith(".txt") else local_path
        request = service.files().get_media(fileId=file_id)

    # Download using MediaIoBaseDownload for large file support
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    with open(local_path, "wb") as f:
        f.write(fh.getvalue())

    return local_path

