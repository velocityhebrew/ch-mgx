import os
import requests
from pathlib import Path

def upload_to_instagram(video_url, caption="Grandmaster Chess Battle"):
    """
    Publishes video to Instagram Reels via Graph API container flow.
    Requires public URL for the video (e.g. hosted temporarily or cloud bucket).
    """
    print("\n" + "=" * 60)
    print("📸 INSTAGRAM UPLOAD")
    print("=" * 60)

    access_token = (os.getenv('INSTAGRAM_ACCESS_TOKEN') or os.getenv('IG_ACCESS_TOKEN', '')).strip()
    account_id = (os.getenv('INSTAGRAM_ACCOUNT_ID') or os.getenv('IG_USER_ID', '')).strip()

    if not access_token or not account_id:
        print("[instagram] ⚠️ Skipping Instagram upload (INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID not set).")
        return {"status": "skipped", "platform": "instagram"}

    print("[instagram] Initiating container creation...")
    container_url = f"https://graph.facebook.com/v19.0/{account_id}/media"
    data = {
        'access_token': access_token,
        'video_url': video_url,
        'caption': caption,
        'media_type': 'REELS'
    }
    res = requests.post(container_url, data=data, timeout=60)
    if res.status_code != 200:
        print(f"[instagram] ❌ Container error: {res.text}")
        return {"status": "error", "platform": "instagram", "error": res.text}

    container_id = res.json().get('id')
    print(f"[instagram] Container created: {container_id}. Publishing...")

    publish_url = f"https://graph.facebook.com/v19.0/{account_id}/media_publish"
    pub_res = requests.post(publish_url, data={'access_token': access_token, 'creation_id': container_id}, timeout=60)
    if pub_res.status_code == 200:
        ig_media_id = pub_res.json().get('id')
        print(f"[instagram] ✅ Reel published! Media ID: {ig_media_id}")
        return {"status": "success", "platform": "instagram", "id": ig_media_id}
    else:
        print(f"[instagram] ❌ Publish error: {pub_res.text}")
        return {"status": "error", "platform": "instagram", "error": pub_res.text}
