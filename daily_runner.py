import os
import sys
import asyncio
import datetime
from generate_chess_video import generate_all
from thumbnail_generator import generate_youtube_thumbnail
from upload.publisher import publish_all

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")

def run_daily_pipeline():
    today_str = datetime.date.today().strftime("%B %d, %Y")
    print("=" * 70)
    print(f"       CHESS AI DAILY MULTI-PLATFORM PUBLISHER - {today_str}")
    print("=" * 70)

    # 1. Generate 10-14 Minute Grandmaster Match Video (1080p 60FPS)
    print("[STEP 1/3] Generating today's Grandmaster Chess Video...")
    asyncio.run(generate_all())

    # 2. Generate High-CTR YouTube Thumbnail
    print("\n[STEP 2/3] Generating YouTube Thumbnail...")
    thumb_path = generate_youtube_thumbnail()

    # 3. Multi-Platform Broadcast (YouTube, Facebook, Instagram)
    video_path = os.path.join(RECORDINGS_DIR, "grandmaster_chess_battle.mp4")
    print("\n[STEP 3/3] Broadcasting to Social Channels...")

    title = f"Kasparov's Immortal: The Greatest Chess Game Ever Played [{today_str}]"
    description = f"""The Greatest Chess Game in History: Garry Kasparov vs Veselin Topalov (Wijk aan Zee 1999).

Featuring the legendary double rook sacrifice (Rxd4!! and Re7+!!) and the historical king hunt across the board.
Analyzed and voiced by Grandmaster AI with real-time tactical commentary, arrows, and strategy breakdowns.

PGN & Moves:
1. e4 d6 2. d4 Nf6 3. Nc3 g6 4. Be3 Bg7 5. Qd2 c6 6. f3 b5 7. Nge2 Nbd7 8. Bh6 Bxh6 9. Qxh6 Bb7 10. a3 e5 11. O-O-O Qe7 12. Kb1 a6 13. Nc1 O-O-O 14. Nb3 exd4 15. Rxd4 c5 16. Rd1 Nb6 17. g3 Kb8 18. Na5 Ba8 19. Bh3 d5 20. Qf4+ Ka7 21. Rhe1 d4 22. Nd5 Nbxd5 23. exd5 Qd6 24. Rxd4!! cxd4 25. Re7+!! Kb6 26. Qxd4+ Kxa5 27. b4+ Ka4 28. Qc3 Qxd5 29. Ra7 Bb7 30. Rxb7 Qc4 31. Qxf6 Kxa3 32. Qxa6+ Kxb4 33. c3+ Kxc3 34. Qa1+ Kd2 35. Qb2+ Kd1 36. Bf1 Rd2 37. Rd7 Rxd7 38. Bxc4 bxc4 39. Qxh8 Rd3 40. Qa8 c3 41. Qa4+ Ke1 42. f4 f5 43. Kc1 Rd2 44. Qa7 1-0

#Chess #Kasparov #ImmortalGame #Stockfish #ChessTactics #Grandmaster #ChessAI #BrilliantMove
"""
    tags = [
        "Chess", "Kasparov", "Immortal Game", "Stockfish", "Grandmaster", 
        "Chess Tactics", "Chess AI", "Chess Strategy", "Rapid Chess", 
        "Brilliant Move", "Magnus Carlsen", "Hikaru Nakamura"
    ]

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
    run_daily_pipeline()
