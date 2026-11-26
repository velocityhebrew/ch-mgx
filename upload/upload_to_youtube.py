import os
import json
import subprocess
import time
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Fallback local token locations
LOCAL_TOKEN_PATHS = [
    r"C:\Users\kreg9\Downloads\kreggscode\open code\bots\youtube refresh tokens bot\token_chess magix.json",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "token.json")
]

DEFAULT_PLAYLIST_TITLE = "Grandmaster Chess AI Battles [Daily 3600+ ELO]"

def get_authenticated_service():
    """Authenticate via GitHub Secrets / Env Vars or local token file."""
    client_id = (os.getenv('YOUTUBE_CLIENT_ID') or os.getenv('YT_CLIENT_ID', '')).strip()
    client_secret = (os.getenv('YOUTUBE_CLIENT_SECRET') or os.getenv('YT_CLIENT_SECRET', '')).strip()
    refresh_token = (os.getenv('YOUTUBE_REFRESH_TOKEN') or os.getenv('YT_REFRESH_TOKEN', '')).strip()

    # If env vars not set, attempt loading from local token JSON
    if not all([client_id, client_secret, refresh_token]):
        for p in LOCAL_TOKEN_PATHS:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    client_id = data.get("client_id", "").strip()
                    client_secret = data.get("client_secret", "").strip()
                    refresh_token = data.get("refresh_token", "").strip()
                    if all([client_id, client_secret, refresh_token]):
                        print(f"[youtube] Loaded credentials from local token file.")
                        break
                except Exception:
                    pass

    if not all([client_id, client_secret, refresh_token]):
        print("[youtube] ⚠️ Missing credentials! Set YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN.")
        return None

    def mask(s): return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else "SET"
    print(f"[youtube] Client ID: {mask(client_id)}")
    print(f"[youtube] Refresh Token: {mask(refresh_token)}")

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube"]
    )

    try:
        creds.refresh(Request())
    except Exception as e:
        print(f"[youtube] ❌ Auth error: {e}")
        return None

    return build('youtube', 'v3', credentials=creds)

def add_video_to_playlist(youtube, video_id, playlist_title=DEFAULT_PLAYLIST_TITLE):
    """Finds or creates the playlist and adds the video to it."""
    try:
        print(f"[youtube] Checking playlists for: '{playlist_title}'...")
        res = youtube.playlists().list(part="snippet", mine=True, maxResults=50).execute()
        playlist_id = None
        for item in res.get("items", []):
            if item["snippet"]["title"].strip().lower() == playlist_title.strip().lower():
                playlist_id = item["id"]
                break

        if not playlist_id:
            print(f"[youtube] Creating new playlist: '{playlist_title}'...")
            new_pl = youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": playlist_title,
                        "description": "Daily Autonomous Grandmaster Chess Battles powered by Stockfish 19 (3600+ ELO) with dual-character commentary."
                    },
                    "status": {"privacyStatus": "public"}
                }
            ).execute()
            playlist_id = new_pl["id"]
            import time
            time.sleep(3)

        print(f"[youtube] Adding video {video_id} to playlist {playlist_id}...")
        import time
        for attempt in range(3):
            try:
                youtube.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {"kind": "youtube#video", "videoId": video_id}
                        }
                    }
                ).execute()
                print("[youtube] ✅ Video successfully added to playlist!")
                break
            except Exception as pe:
                if attempt < 2:
                    time.sleep(4)
                else:
                    raise pe
    except Exception as e:
        print(f"[youtube] ⚠️ Playlist notice: {e}")

def probe_duration(path):
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            text=True,
        )
        return float(out.strip())
    except Exception:
        return None


def upload_captions(youtube, video_id, srt_path):
    """Upload the generated SRT as English closed captions (retries while YouTube processes)."""
    if not srt_path or not os.path.exists(srt_path):
        return
    print(f"[youtube] Uploading captions: {srt_path}...")
    last_err = None
    for attempt in range(3):
        try:
            youtube.captions().insert(
                part="snippet",
                body={"snippet": {
                    "videoId": video_id,
                    "language": "en",
                    "name": "English",
                    "isDraft": False,
                }},
                media_body=MediaFileUpload(str(srt_path), mimetype="application/octet-stream", resumable=False),
            ).execute()
            print("[youtube] ✅ Captions uploaded successfully!")
            return
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(6)
    print(f"[youtube] ⚠️ Caption upload notice: {last_err}")


def sanitize_youtube_title(raw_title, max_len=95):
    """Sanitizes title to conform strictly to YouTube API rules (<100 chars, no angle brackets)."""
    if not raw_title:
        return "Grandmaster Chess Showdown | Daily Battle"
    t = str(raw_title).replace("<", "").replace(">", "").strip()
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
    if len(t) > max_len:
        t = t[:max_len-3].rstrip() + "..."
    return t

def _insert_video(youtube, body, video_path):
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  -> Upload progress: {int(status.progress() * 100)}%")
    return resp


def upload_to_youtube(video_path, thumbnail_path=None, title=None, description=None, tags=None,
                      playlist_title=DEFAULT_PLAYLIST_TITLE, privacy_status="public", srt_path=None,
                      add_to_playlist=True, publish_at=None):
    """Full YouTube upload with custom thumbnail, captions, and playlist insertion."""
    print("\n" + "=" * 60)
    print("▶️ YOUTUBE UPLOAD INITIATED")
    print("=" * 60)

    youtube = get_authenticated_service()
    if not youtube:
        print("[youtube] ⚠️ Skipping YouTube upload (no valid credentials).")
        return {"status": "skipped", "platform": "youtube"}

    if title is None:
        title = "Stockfish 19 Grandmaster Chess Showdown | Sicilian Defense Najdorf"

    safe_title = sanitize_youtube_title(title)

    if tags is None:
        tags = [
            "Chess", "Stockfish 19", "Grandmaster Chess", "Sicilian Defense", 
            "Chess AI", "Chess Tactics", "Chess Strategy", "Rapid Blitz", 
            "Brilliant Move", "Magnus Carlsen", "Hikaru Nakamura", "Chess.com"
        ]

    duration = probe_duration(video_path)
    if duration is not None:
        print(f"[youtube] Video duration: {duration / 60:.1f} minutes ({duration:.0f}s)")
        if duration < 120:
            print("[youtube] ⚠️ WARNING: video is under 2 minutes — check the generator output.")

    body = {
        "snippet": {
            "title": safe_title,
            "description": description or "Daily Grandmaster Chess Match generated with Stockfish 19.",
            "tags": tags,
            "categoryId": "20",  # Gaming
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": "private" if publish_at else privacy_status,
            "selfDeclaredMadeForKids": False,
            # AI voice + generated visuals: disclose synthetic/altered content.
            "containsSyntheticMedia": True,
        }
    }
    if publish_at:
        body["status"]["publishAt"] = publish_at
        print(f"[youtube] Scheduling for {publish_at}")

    print(f"[youtube] Uploading: {title} ({os.path.getsize(video_path) // (1024*1024)} MB)...")
    resp = None
    for _ in range(3):
        try:
            resp = _insert_video(youtube, body, video_path)
            break
        except HttpError as e:
            msg = str(e)
            if "containsSyntheticMedia" in msg and "containsSyntheticMedia" in body["status"]:
                print("[youtube] Retrying without synthetic-media flag (API rejected the field)...")
                body["status"].pop("containsSyntheticMedia", None)
                continue
            if ("publishAt" in msg or "privacyStatus" in msg) and "publishAt" in body["status"]:
                print("[youtube] Scheduled publishing rejected; publishing immediately instead...")
                body["status"].pop("publishAt", None)
                body["status"]["privacyStatus"] = "public"
                continue
            raise
    if resp is None:
        raise RuntimeError("YouTube upload failed after metadata fallbacks")

    video_id = resp.get("id")
    video_url = f"https://youtu.be/{video_id}"
    print(f"[youtube] ✅ Video published successfully! URL: {video_url}")

    # Upload Custom Thumbnail
    if thumbnail_path and os.path.exists(thumbnail_path):
        print(f"[youtube] Uploading custom thumbnail: {thumbnail_path}...")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png")
            ).execute()
            print("[youtube] ✅ Custom thumbnail set successfully!")
        except Exception as e:
            print(f"[youtube] ⚠️ Thumbnail error: {e}")

    # Upload English closed captions
    upload_captions(youtube, video_id, srt_path)

    # Add to Playlist (long-form only; Shorts should not go into the long playlist)
    if add_to_playlist:
        add_video_to_playlist(youtube, video_id, playlist_title)

    return {
        "status": "success",
        "platform": "youtube",
        "video_id": video_id,
        "url": video_url,
        "scheduled": bool(body["status"].get("publishAt")),
        "publish_at": body["status"].get("publishAt"),
    }
