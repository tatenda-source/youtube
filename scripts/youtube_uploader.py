"""
YouTube Uploader — auto-upload videos, thumbnails, and Shorts to YouTube.
Uses YouTube Data API v3 with OAuth 2.0.

First run will open a browser for Google login — after that, the token is cached.
"""

import json
import os
import sys
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BASE_DIR

# YouTube API scopes
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

CLIENT_SECRET_FILE = BASE_DIR / "client_secret.json"
TOKEN_FILE = BASE_DIR / "token.json"

# YouTube category IDs
CATEGORIES = {
    "education": "27",
    "entertainment": "24",
    "science": "28",
    "people": "22",
    "howto": "26",
    "news": "25",
}


def get_authenticated_service():
    """Authenticate and return a YouTube API service object."""
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET_FILE.exists():
                raise FileNotFoundError(
                    f"Missing {CLIENT_SECRET_FILE}\n"
                    "Download OAuth credentials from Google Cloud Console:\n"
                    "  1. console.cloud.google.com → APIs & Services → Credentials\n"
                    "  2. Create OAuth 2.0 Client ID (Desktop app)\n"
                    "  3. Download JSON → rename to client_secret.json\n"
                    "  4. Place in project root"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_FILE), SCOPES
            )
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags: list = None,
    category: str = "education",
    privacy: str = "public",
    is_short: bool = False,
    publish_at: str = None,
) -> str:
    """
    Upload a video to YouTube.

    Args:
        video_path: Path to the video file
        title: Video title
        description: Video description
        tags: List of tags
        category: Category name (education, entertainment, etc.)
        privacy: "public", "unlisted", or "private"
        is_short: If True, adds #Shorts to title
        publish_at: ISO 8601 datetime for scheduled publish (e.g. "2026-03-25T15:00:00Z")

    Returns:
        Video ID of the uploaded video
    """
    youtube = get_authenticated_service()

    if is_short and "#Shorts" not in title:
        title = f"{title} #Shorts"

    # Truncate title to YouTube's 100 char limit
    if len(title) > 100:
        title = title[:97] + "..."

    category_id = CATEGORIES.get(category, "27")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy if not publish_at else "private",
            "selfDeclaredMadeForKids": False,
        },
    }

    # Schedule for later if publish_at is set
    if publish_at:
        body["status"]["publishAt"] = publish_at
        body["status"]["privacyStatus"] = "private"

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    print(f"  Uploading: {title}")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"  Upload progress: {pct}%")

    video_id = response["id"]
    print(f"  Uploaded! Video ID: {video_id}")
    print(f"  URL: https://youtube.com/watch?v={video_id}")

    return video_id


def set_thumbnail(video_id: str, thumbnail_path: str) -> bool:
    """Upload a custom thumbnail for a video."""
    youtube = get_authenticated_service()

    try:
        media = MediaFileUpload(thumbnail_path, mimetype="image/png")
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=media,
        ).execute()
        print(f"  Thumbnail set for {video_id}")
        return True
    except Exception as e:
        print(f"  Warning: Thumbnail upload failed: {e}")
        print("  (Custom thumbnails require a verified account)")
        return False


def upload_with_thumbnail(
    video_path: str,
    thumbnail_path: str,
    title: str,
    description: str = "",
    tags: list = None,
    category: str = "education",
    privacy: str = "public",
    is_short: bool = False,
    publish_at: str = None,
) -> str:
    """Upload a video and set its custom thumbnail."""
    video_id = upload_video(
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        category=category,
        privacy=privacy,
        is_short=is_short,
        publish_at=publish_at,
    )

    # Wait a moment for YouTube to process
    time.sleep(3)

    if thumbnail_path and Path(thumbnail_path).exists():
        set_thumbnail(video_id, thumbnail_path)

    return video_id


def upload_pipeline_output(result: dict, privacy: str = "public", publish_at: str = None) -> dict:
    """
    Upload all outputs from a pipeline run.
    Takes the result dict returned by pipeline.run_pipeline().
    """
    uploaded = {}

    # Upload long-form video
    if result.get("video_path") and Path(result["video_path"]).exists():
        print("\n[UPLOAD] Long-form video...")
        video_id = upload_with_thumbnail(
            video_path=result["video_path"],
            thumbnail_path=result.get("thumbnail_path", ""),
            title=result["title"],
            description=result.get("description", ""),
            tags=result.get("tags", []),
            privacy=privacy,
            publish_at=publish_at,
        )
        uploaded["video_id"] = video_id
        uploaded["video_url"] = f"https://youtube.com/watch?v={video_id}"

    return uploaded


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--tags", nargs="+", default=[], help="Video tags")
    parser.add_argument("--thumbnail", help="Path to thumbnail image")
    parser.add_argument("--privacy", choices=["public", "unlisted", "private"], default="public")
    parser.add_argument("--short", action="store_true", help="Mark as YouTube Short")
    parser.add_argument("--schedule", help="Schedule publish (ISO 8601: 2026-03-25T15:00:00Z)")

    args = parser.parse_args()

    if args.thumbnail:
        upload_with_thumbnail(
            video_path=args.video,
            thumbnail_path=args.thumbnail,
            title=args.title,
            description=args.description,
            tags=args.tags,
            privacy=args.privacy,
            is_short=args.short,
            publish_at=args.schedule,
        )
    else:
        upload_video(
            video_path=args.video,
            title=args.title,
            description=args.description,
            tags=args.tags,
            privacy=args.privacy,
            is_short=args.short,
            publish_at=args.schedule,
        )
