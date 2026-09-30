import os
import sys
import asyncio
import datetime
from generate_chess_video import generate_all
from thumbnail_generator import generate_youtube_thumbnail
from upload.publisher import publish_all
from grandmaster_database import get_game_of_the_day
from commentary_ai import select_daily_grandmaster_game, generate_game_metadata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")

def run_daily_pipeline(requested_game_id=None):
    today_str = datetime.date.today().strftime("%B %d, %Y")
    
    # 1. Dynamically Select Today's Grandmaster Game via AI / Verified Rotation
    game_info = select_daily_grandmaster_game(requested_game_id)
    white_player = game_info.get("white_name", "White")
    black_player = game_info.get("black_name", "Black")
    event = game_info.get("event", "Championship")
    opening = game_info.get("opening", "Grandmaster Theory")
    theme = game_info.get("theme", "Immortal Game")

    print("=" * 70)
    print(f"       CHESS AI DAILY MULTI-PLATFORM PUBLISHER - {today_str}")
    print("=" * 70)
    print(f"Game of the Day : {game_info['title']}")
    print(f"Matchup         : {white_player} vs {black_player}")
    print(f"Event           : {event}")
    print(f"Opening         : {opening}")
    print(f"Tactical Theme  : {theme}")
    print("=" * 70)

    # 2. Query Paid Pollinations AI for Viral Metadata & Hooks
    print("\n[AI METADATA] Generating dynamic YouTube/Facebook metadata via Pollinations AI...")
    ai_meta = generate_game_metadata(game_info, today_str)
    title = ai_meta.get("title", f"{white_player} vs {black_player}: {theme} [{today_str}]")
    hook = ai_meta.get("hook_summary", f"Relive the historic battle between {white_player} and {black_player} at {event}.")
    tags = ai_meta.get("tags", [white_player, black_player, "Chess", "Grandmaster", opening, "Brilliant Move", "Stockfish"])

    print(f"Title: {title}")

    # 3. Generate Grandmaster Match Video (1080p 60FPS)
    print("\n[STEP 1/3] Generating today's Grandmaster Chess Video...")
    asyncio.run(generate_all(game_info))

    # 4. Generate High-CTR YouTube Thumbnail
    print("\n[STEP 2/3] Generating High-CTR Thumbnail...")
    thumb_path = generate_youtube_thumbnail(game_info)

    # 5. Multi-Platform Broadcast (YouTube & Facebook)
    video_path = os.path.join(RECORDINGS_DIR, "grandmaster_chess_battle.mp4")
    print("\n[STEP 3/3] Broadcasting to Social Channels...")

    description = f"""{title}

{hook}

Match Information:
* White: {white_player} ({game_info.get('white_rating', '2800')})
* Black: {black_player} ({game_info.get('black_rating', '2800')})
* Event: {event}
* Opening: {opening}
* Theme: {theme}

Full PGN & Moves:
{game_info.get('pgn', '')}

Analyzed by Stockfish 19 & Voiced by Grandmaster AI with real-time tactical evaluation, board annotations, and live clocks.

#Chess #Grandmaster #{white_player.replace(' ', '')} #{black_player.replace(' ', '')} #ChessTactics #ChessAI #BrilliantMove #ChessMagix
"""

    results = publish_all(
        video_path=video_path,
        thumbnail_path=thumb_path,
        title=title,
        description=description,
        tags=tags
    )
    print("\n" + "=" * 70)
    print("DAILY PIPELINE COMPLETE!")
    print(f"Publishing Results: {results}")
    print("=" * 70)

if __name__ == "__main__":
    game_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_daily_pipeline(game_arg)
