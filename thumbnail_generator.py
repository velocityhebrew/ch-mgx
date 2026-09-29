"""
Dynamic Grandmaster YouTube Thumbnail Generator
Renders high-CTR, dramatic board climax states for whichever game is selected for the day.
Enhanced with dynamic AI hooks, badges, and player names.
"""

import os
import chess
from PIL import Image, ImageDraw, ImageFont
from board_renderer import ChessBoardRenderer, find_font
from grandmaster_database import get_game_of_the_day, parse_game_moves
from commentary_ai import generate_thumbnail_copy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
THUMBNAIL_PATH = os.path.join(RECORDINGS_DIR, "thumbnail.png")

def generate_youtube_thumbnail(game_info=None):
    if not game_info:
        game_info = get_game_of_the_day()

    print(f"[*] Generating high-CTR YouTube thumbnail for: {game_info['title']}...")
    renderer = ChessBoardRenderer()

    moves = parse_game_moves(game_info)
    climax_ply = min(game_info.get("climax_ply", 30), len(moves))
    board = chess.Board()
    history = []

    for i, m in enumerate(moves[:climax_ply]):
        move_obj = chess.Move.from_uci(m["move"])
        board.push(move_obj)
        num = (i + 2) // 2
        if m["player"] == "White":
            history.append({"num": num, "white": m["san"], "black": "...", "eval": m["eval"]})
        else:
            if history:
                history[-1]["black"] = m["san"]
                history[-1]["eval"] = m["eval"]

    last_move = chess.Move.from_uci(moves[climax_ply - 1]["move"]) if climax_ply > 0 else None
    
    climax_move = moves[climax_ply - 1]
    
    # Query AI for thumbnail hook & badges
    ai_copy = generate_thumbnail_copy(game_info)
    top_hook = ai_copy.get("top_banner", f"STOCKFISH 19 (3600+ ELO) IMMORTAL BATTLE").upper()
    badge_text = ai_copy.get("badge", game_info.get("climax_badge", "!! BRILLIANT MOVE")).upper()
    callout_text = ai_copy.get("bottom_callout", game_info.get("climax_hook", "GREATEST MOVE IN CHESS HISTORY?!")).upper()

    frame = renderer.render_frame(
        board=board,
        last_move=last_move,
        move_history=history[-12:],
        white_clock="06:12",
        black_clock="06:34",
        active_player=climax_move["player"],
        eval_score=climax_move["eval"],
        subtitle_text=climax_move["dialogue"],
        strategy_name=climax_move["strategy"],
        white_name=game_info.get("white_name", "White"),
        black_name=game_info.get("black_name", "Black"),
        white_title=f"Grandmaster  |  Rating: {game_info.get('white_rating', '2800')}  |  Pieces: White",
        black_title=f"Grandmaster  |  Rating: {game_info.get('black_rating', '2800')}  |  Pieces: Black"
    )

    draw = ImageDraw.Draw(frame)

    impact_sub = find_font("bold", 28)
    badge_font = find_font("bold", 34)

    # Top YouTube Hook Banner
    draw.rectangle([940, 15, 1772, 60], fill=(220, 20, 60))
    draw.text((960, 18), top_hook[:48], font=impact_sub, fill=(255, 255, 255))

    # Climax Badge on Board
    badge_w = min(460, len(badge_text) * 22 + 40)
    badge_x, badge_y = 960, 85
    draw.rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + 60], fill=(0, 200, 255), outline=(255, 255, 255), width=3)
    draw.text((badge_x + 18, badge_y + 10), badge_text, font=badge_font, fill=(0, 0, 0))

    # Bottom Callout Banner
    callout_y = 860
    draw.rectangle([940, callout_y, 1772, callout_y + 55], fill=(218, 165, 32), outline=(255, 255, 255), width=2)
    draw.text((960, callout_y + 10), callout_text[:46], font=impact_sub, fill=(0, 0, 0))

    frame.save(THUMBNAIL_PATH)
    print(f"[SUCCESS] YouTube thumbnail generated at: {THUMBNAIL_PATH}")
    return THUMBNAIL_PATH

if __name__ == "__main__":
    generate_youtube_thumbnail()
