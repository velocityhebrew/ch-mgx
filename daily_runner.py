import os
import re
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


def format_chapter_time(seconds):
    total = max(0, int(seconds))
    return f"{total // 60}:{total % 60:02d}"


def hashtag(name):
    return re.sub(r"[^A-Za-z0-9]", "", str(name).replace("GM ", ""))


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

    # 1b. Real Stockfish analysis (falls back to simulated evals if unavailable)
    print("\n[STOCKFISH] Analysing today's game...")
    try:
        from stockfish_analysis import analyse_game
        analysis = analyse_game(game_info)
        if analysis:
            game_info["stockfish_analysis"] = analysis
            if game_info.get("source") == "chess.com":
                game_info["climax_ply"] = analysis["climax_ply"]
                game_info["climax_badge"] = analysis["climax_badge"]
                game_info["climax_hook"] = analysis["climax_hook"]
            print(
                f"[STOCKFISH] {analysis['engine']} depth {analysis['depth']} | "
                f"turning point ply {analysis['climax_ply']}"
            )
        else:
            print("[STOCKFISH] Unavailable; keeping simulated evaluations.")
    except Exception as e:
        print(f"[STOCKFISH] Analysis skipped: {e}")

    # 2. Query Paid Pollinations AI for Viral Metadata & Hooks
    print("\n[AI METADATA] Generating dynamic YouTube/Facebook metadata via Pollinations AI...")
    ai_meta = generate_game_metadata(game_info, today_str)
    title = ai_meta.get("title", f"{white_player} vs {black_player}: {theme} [{today_str}]")
    hook = ai_meta.get("hook_summary", "")
    if not isinstance(hook, str) or not hook.strip():
        hook = f"Relive the historic battle between {white_player} and {black_player} at {event}."
    game_info["story_summary"] = hook.strip()

    raw_tags = ai_meta.get("tags", [])
    if isinstance(raw_tags, str):
        raw_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
    elif not isinstance(raw_tags, list):
        raw_tags = []
    tags = raw_tags or [white_player, black_player, "Chess", "Grandmaster", opening, "Brilliant Move", "Stockfish"]
    tags = list(dict.fromkeys(
        [str(t) for t in tags] +
        ["chess full game", "grandmaster chess", "chess analysis", "chess history",
         "brilliant move", "chess magix", white_player, black_player, opening]
    ))
    # YouTube rejects tag sets over 500 characters; keep a safe margin.
    trimmed, used = [], 0
    for tag in tags:
        tag = str(tag).strip()
        if not tag:
            continue
        if used + len(tag) + 1 > 480:
            break
        trimmed.append(tag)
        used += len(tag) + 1
    tags = trimmed

    print(f"Title: {title}")

    # 3. Generate Grandmaster Match Video (1080p 60FPS, full game)
    print("\n[STEP 1/3] Generating today's Grandmaster Chess Video...")
    render_result = asyncio.run(generate_all(game_info))
    video_path = render_result["video_path"]
    srt_path = render_result.get("subtitles") or os.path.join(RECORDINGS_DIR, "chess_subtitles.srt")
    chapters = render_result.get("chapters", [])
    print(f"[INFO] Full game rendered: {render_result.get('duration', 0):.1f}s, {len(chapters)} chapters")

    # 4. Generate High-CTR YouTube Thumbnail
    print("\n[STEP 2/3] Generating High-CTR Thumbnail...")
    thumb_path = generate_youtube_thumbnail(game_info)

    # 4b. Generate up to three vertical YouTube Shorts from the same game
    print("\n[STEP 2b/3] Generating today's YouTube Shorts...")
    short_infos = []
    try:
        from shorts_generator import generate_all_shorts
        short_infos = asyncio.run(generate_all_shorts(game_info))
        print(f"[INFO] {len(short_infos)} Shorts ready: "
              + ", ".join(f"{s['moment']} {s['duration']:.1f}s" for s in short_infos))
    except Exception as e:
        print(f"[short] Generation skipped: {e}")

    # 5. Multi-Platform Broadcast (YouTube & Facebook)
    print("\n[STEP 3/3] Broadcasting to Social Channels...")
    if not os.path.exists(video_path) or os.path.getsize(video_path) < 1_000_000:
        raise RuntimeError(f"Video file is missing or suspiciously small: {video_path}")

    chapter_lines = "\n".join(
        f"{format_chapter_time(ch.get('time', 0))} {ch.get('title', 'Highlights')}"
        for ch in chapters
    )

    stockfish_info = game_info.get("stockfish_analysis") or {}
    if stockfish_info:
        analysis_line = (
            f"Analyzed with {stockfish_info.get('engine', 'Stockfish')} "
            f"at depth {stockfish_info.get('depth', '?')}"
        )
    else:
        analysis_line = "Analyzed with Stockfish-compatible evaluation"

    description = f"""{title}

{hook}

⏱ CHAPTERS
{chapter_lines}

MATCH INFORMATION
* White: {white_player} ({game_info.get('white_rating', '2800')})
* Black: {black_player} ({game_info.get('black_rating', '2800')})
* Event: {event}
* Opening: {opening}
* Theme: {theme}
* Result: {game_info.get('pgn', '').strip().split()[-1] if game_info.get('pgn') else 'Classic'}

🔔 Subscribe for a new grandmaster masterpiece every day.
💬 Comment your favorite move below.

FULL PGN & MOVES
{game_info.get('pgn', '')}

{analysis_line} and voiced by the Chess Magix broadcast team, with real tactical evaluation, board annotations, and live clocks.

#Chess #Grandmaster #{hashtag(white_player)} #{hashtag(black_player)} #ChessTactics #ChessAI #BrilliantMove #ChessMagix
"""

    results = publish_all(
        video_path=video_path,
        thumbnail_path=thumb_path,
        title=title,
        description=description,
        tags=tags,
        srt_path=srt_path,
    )

    # 6. Upload the Shorts after the long video so we can link to it.
    #    Spread them across the day: +1h, +5h, +9h.
    long_url = (results.get("youtube") or {}).get("url")
    if short_infos and long_url:
        from upload.upload_to_youtube import upload_to_youtube
        offsets = [1, 3, 5]
        for i, info in enumerate(short_infos):
            key = f"youtube_short_{i + 1}"
            print(f"\n[STEP 3b/3] Uploading Short {i + 1}/{len(short_infos)} "
                  f"({info['moment']})...")
            try:
                publish_at = (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(hours=offsets[i])
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
                short_desc = f"{info['description']}\n\nFull game: {long_url}"
                results[key] = upload_to_youtube(
                    video_path=info["path"],
                    thumbnail_path=None,
                    title=info["title"],
                    description=short_desc,
                    tags=tags,
                    srt_path=info.get("srt"),
                    add_to_playlist=False,
                    publish_at=publish_at,
                )
            except Exception as e:
                print(f"[short] Upload error: {e}")
                results[key] = {"status": "error", "error": str(e)}
    elif short_infos:
        print("[short] Long upload was skipped or failed; Short uploads skipped.")

    print("\n" + "=" * 70)
    print("DAILY PIPELINE COMPLETE!")
    print(f"Publishing Results: {results}")
    print("=" * 70)

if __name__ == "__main__":
    game_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_daily_pipeline(game_arg)
