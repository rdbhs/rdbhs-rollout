import os
import pickle
from datetime import datetime
from pathlib import Path

import duckdb
import yaml
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from rollout.config import SeederConfig

SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_token(secret_files_path: Path):
    token_path = secret_files_path / "token.pkl"
    token = None
    if token_path.exists():
        with token_path.open("rb") as token_file:
            token = pickle.load(token_file)
    if not token or not token.valid:
        if token and token.expired and token.refresh_token:
            token.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(secret_files_path / "google_credentials.json"), SCOPES
            )
            token = flow.run_local_server(port=0)
        with token_path.open("wb") as token_file:
            pickle.dump(token, token_file)
    return token


def run(
    connection: duckdb.DuckDBPyConnection,
    staging_dir: Path,
) -> dict[str, duckdb.DuckDBPyRelation]:
    seeder_path = Path(__file__).resolve()
    root = seeder_path.parent.parent
    load_dotenv(root / ".env", override=False)
    config = SeederConfig.model_validate(
        yaml.safe_load(seeder_path.with_suffix(".yaml").read_text())
    )
    secret_files_path = root / os.environ.get("SECRET_FILES_PATH", "secrets")
    service = build("drive", "v3", credentials=get_token(secret_files_path))

    results = {}
    for output in config.outputs:
        base_name = output.removeprefix("alleva_")
        files = []
        page_token = None
        while True:
            response = (
                service.files()
                .list(
                    q=f"name = '{base_name}.csv' and trashed = false",
                    fields="nextPageToken, files(id, name, modifiedTime)",
                    pageToken=page_token,
                )
                .execute()
            )
            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        if not files:
            raise ValueError(f"No Google Drive export available for {output}")
        files.sort(
            key=lambda item: (item.get("modifiedTime", ""), item["name"], item["id"])
        )

        folder = staging_dir / output
        folder.mkdir(parents=True, exist_ok=True)
        for item in files:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            destination = folder / f"{Path(item['name']).stem}_{timestamp}.csv"
            with destination.open("xb") as handle:
                downloader = MediaIoBaseDownload(
                    handle, service.files().get_media(fileId=item["id"])
                )
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                handle.flush()
                os.fsync(handle.fileno())

            results[output] = connection.read_csv(
                str(destination),
                header=True,
                strict_mode=False,
                ignore_errors=True,
                store_rejects=True,
                normalize_names=True,
                filename=True,
            )
            service.files().delete(fileId=item["id"]).execute()

    return results
