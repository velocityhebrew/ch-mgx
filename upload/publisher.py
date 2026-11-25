import os
from .upload_to_youtube import upload_to_youtube
from .upload_facebook import upload_to_facebook

# Note: Instagram publishing is disabled to prevent unnecessary Graph API calls and rate-limiting.
# Publishing exclusively to YouTube and Facebook.

def publish_all(video_path, thumbnail_path=None, title=None, description=None, tags=None, srt_path=None):
    """Orchestrates multi-platform publishing to YouTube, Facebook, and Instagram."""
    print("=" * 70)
    print("       MULTI-PLATFORM AUTOMATED SOCIAL BROADCAST")
    print("=" * 70)

    results = {}

    if os.getenv("DRY_RUN", "").strip().lower() in ("true", "1", "yes"):
        print("[publisher] DRY_RUN enabled — generation only, skipping all uploads.")
        return {
            "youtube": {"status": "dry_run"},
            "facebook": {"status": "dry_run"},
        }

    # 1. YouTube (with playlist & custom thumbnail)
    upload_yt_env = os.getenv("UPLOAD_YOUTUBE", "true").lower()
    if upload_yt_env in ("false", "0", "no"):
        print("[publisher] ⏸️ Skipping YouTube upload (UPLOAD_YOUTUBE=false). Facebook upload will proceed.")
        results['youtube'] = {"status": "skipped", "reason": "UPLOAD_YOUTUBE=false"}
    else:
        try:
            results['youtube'] = upload_to_youtube(
                video_path=video_path,
                thumbnail_path=thumbnail_path,
                title=title,
                description=description,
                tags=tags,
                srt_path=srt_path,
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
