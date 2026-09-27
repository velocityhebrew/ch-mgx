import os
import sys
import asyncio
import datetime
from generate_chess_video import generate_all
from thumbnail_generator import generate_youtube_thumbnail
from youtube_uploader import upload_video

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")

def run_daily_pipeline():
    today_str = datetime.date.today().strftime("%B %d, %Y")
    print("=" * 70)
    print(f"       CHESS AI DAILY YOUTUBE AUTOMATION PIPELINE - {today_str}")
    print("=" * 70)

    # 1. Generate Match Video & Dual Voiceover
    print("[STEP 1/3] Generating today's Grandmaster Chess Video...")
    asyncio.run(generate_all())

    # 2. Generate Eye-Catching YouTube Thumbnail
    print("\n[STEP 2/3] Generating YouTube Thumbnail...")
    thumb_path = generate_youtube_thumbnail()

    # 3. Check for YouTube Upload
    video_path = os.path.join(RECORDINGS_DIR, "grandmaster_chess_battle.mp4")
    print("\n[STEP 3/3] Preparing YouTube Upload...")
    title = f"Stockfish 19 vs Grandmaster: Masterclass Chess Battle [{today_str}]"
    description = f"""Daily Autonomous Grandmaster Chess Battle generated with Stockfish 19 (3600+ ELO).

Opening: Sicilian Defense: Najdorf / English Attack
Featuring dual-character grandmaster commentary (GM Alexander vs GM Victor).
Full game notation, tactical sacrifice breakdown, and checkmate finish.

#Chess #Stockfish #Grandmaster #SicilianDefense #ChessTactics #AI
"""
    tags = ["Chess", "Stockfish", "Grandmaster", "Sicilian Defense", "Chess AI", "Chess Tactics", "Rapid Blitz"]

    if os.path.exists(os.path.join(BASE_DIR, "client_secrets.json")) or os.path.exists(os.path.join(BASE_DIR, "token.json")):
        upload_video(video_path, thumbnail_path=thumb_path, title=title, description=description, tags=tags)
    else:
        print("[!] No client_secrets.json found yet.")
        print("[+] Video and Thumbnail are rendered locally and ready for upload!")

if __name__ == "__main__":
    run_daily_pipeline()
