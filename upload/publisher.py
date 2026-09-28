import os
from .upload_to_youtube import upload_to_youtube
from .upload_facebook import upload_to_facebook

# Note: Instagram publishing is disabled to prevent unnecessary Graph API calls and rate-limiting.
# Publishing exclusively to YouTube and Facebook.

def publish_all(video_path, thumbnail_path=None, title=None, description=None, tags=None):
    """Orchestrates multi-platform publishing to YouTube, Facebook, and Instagram."""
    print("=" * 70)
    print("       MULTI-PLATFORM AUTOMATED SOCIAL BROADCAST")
    print("=" * 70)

    results = {}

    # 1. YouTube (with playlist & custom thumbnail)
    try:
        results['youtube'] = upload_to_youtube(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            title=title,
            description=description,
            tags=tags
        )
    except Exception as e:
        print(f"[publisher] YouTube error: {e}")
        results['youtube'] = {"status": "error", "error": str(e)}

    # 2. Facebook
    try:
        results['facebook'] = upload_to_facebook(
            video_path=video_path,
            description=description or title or "Grandmaster Chess AI",
            title=title or "Grandmaster Chess AI"
        )
    except Exception as e:
        print(f"[publisher] Facebook error: {e}")
        results['facebook'] = {"status": "error", "error": str(e)}

    return results
