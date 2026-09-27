import os
import requests
from pathlib import Path

def upload_to_facebook(video_path, description, title="Grandmaster Chess AI"):
    """Uploads video to Facebook Page using Graph API."""
    print("\n" + "=" * 60)
    print("📘 FACEBOOK UPLOAD")
    print("=" * 60)

    access_token = (os.getenv('FACEBOOK_ACCESS_TOKEN') or os.getenv('FB_ACCESS_TOKEN', '')).strip()
    page_id = (os.getenv('FACEBOOK_PAGE_ID') or os.getenv('FB_PAGE_ID', '')).strip()

    if not access_token or not page_id:
        print("[facebook] ⚠️ Skipping Facebook upload (FACEBOOK_ACCESS_TOKEN or FACEBOOK_PAGE_ID not set).")
        return {"status": "skipped", "platform": "facebook"}

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        print(f"[facebook] ❌ File not found: {video_path}")
        return {"status": "error", "platform": "facebook"}

    url = f"https://graph-video.facebook.com/v19.0/{page_id}/videos"
    print(f"[facebook] Uploading video to Page {page_id}...")
    
    with open(video_path, 'rb') as f:
        files = {'source': f}
        data = {
            'access_token': access_token,
            'title': title,
            'description': description
        }
        res = requests.post(url, files=files, data=data, timeout=300)
    
    if res.status_code == 200:
        vid_id = res.json().get('id')
        print(f"[facebook] ✅ Video uploaded successfully! Video ID: {vid_id}")
        return {"status": "success", "platform": "facebook", "id": vid_id}
    else:
        print(f"[facebook] ❌ Error: {res.text}")
        return {"status": "error", "platform": "facebook", "error": res.text}
