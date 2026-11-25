"""
Dynamic Grandmaster YouTube Thumbnail Generator
Renders high-CTR, dramatic board climax states for whichever game is selected for the day.
Enhanced with dynamic AI hooks, badges, and player names.
"""

import os
import chess
from PIL import Image, ImageDraw, ImageFont
from board_renderer import ChessBoardRenderer, find_font, wrap_text
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

    def has_plain_words(value):
        cleaned = str(value).replace("!", "").replace("+", "").replace("#", "")
        return any(len(w) >= 4 and w.isalpha() for w in cleaned.split())

    def safe_text(value, fallback, limit):
        if not isinstance(value, str) or not value.strip() or not has_plain_words(value):
            value = fallback
        return value.strip().upper()[:limit]

    def display_name(name):
        n = str(name).replace("GM ", "").split("&")[0].strip()
        return n.upper()

    top_hook = safe_text(
        f"{display_name(game_info.get('white_name', 'White'))} VS {display_name(game_info.get('black_name', 'Black'))}",
        "IMMORTAL GRANDMASTER BATTLE",
        52,
    )
    badge_text = safe_text(ai_copy.get("badge"), game_info.get("climax_badge", "!! BRILLIANT MOVE"), 42)
    callout_text = safe_text(ai_copy.get("bottom_callout"), game_info.get("climax_hook", "GREATEST MOVE IN CHESS HISTORY?!"), 90)

    frame = renderer.render_frame(
        board=board,
        last_move=last_move,
        move_history=history[-12:],
        white_clock="06:12",
        black_clock="06:34",
        active_player=climax_move["player"],
        eval_score=climax_move["eval"],
        subtitle_text="",
        strategy_name=climax_move["strategy"],
        white_name=game_info.get("white_name", "White"),
        black_name=game_info.get("black_name", "Black"),
        white_title=f"Grandmaster  •  {game_info.get('white_rating', '2800')}  •  White",
        black_title=f"Grandmaster  •  {game_info.get('black_rating', '2800')}  •  Black",
        event_name="",
        progress=climax_ply / max(1, len(moves)),
        show_replay_badge=False,
    )

    draw = ImageDraw.Draw(frame)

    impact_sub = find_font("bold", 30)
    badge_font = find_font("bold", 34)
    callout_font = find_font("bold", 36)

    # Top hook banner across the header (brand stays visible on the left)
    while draw.textlength(top_hook, font=impact_sub) > 1100 and impact_sub.size > 20:
        impact_sub = find_font("bold", impact_sub.size - 2)
    draw.rounded_rectangle([400, 8, 1560, 56], radius=12, fill=(200, 30, 45), outline=(255, 255, 255), width=2)
    draw.text((420, 15), top_hook, font=impact_sub, fill=(255, 255, 255),
              stroke_width=2, stroke_fill=(90, 0, 10))

    # Climax badge on the board's top-left corner
    while draw.textlength(badge_text, font=badge_font) > 560 - 44 and badge_font.size > 20:
        badge_font = find_font("bold", badge_font.size - 2)
    badge_w = draw.textlength(badge_text, font=badge_font) + 44
    badge_x, badge_y = 1052, 104
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + 62],
                           radius=12, fill=(232, 184, 66), outline=(255, 255, 255), width=3)
    draw.text((badge_x + 22, badge_y + 12), badge_text, font=badge_font, fill=(15, 18, 24))

    # Bottom callout replaces the commentary banner (wraps, never shrinks)
    draw.rounded_rectangle([48, 950, 1872, 1054], radius=16, fill=(232, 184, 66))
    lines = wrap_text(draw, callout_text, callout_font, 1760)[:2]
    line_h = 44
    ty = 950 + (104 - line_h * len(lines)) // 2 + 4
    for ln in lines:
        cw = draw.textlength(ln, font=callout_font)
        draw.text((960 - cw / 2, ty), ln, font=callout_font, fill=(15, 18, 24))
        ty += line_h

    frame.save(THUMBNAIL_PATH)
    print(f"[SUCCESS] YouTube thumbnail generated at: {THUMBNAIL_PATH}")
    return THUMBNAIL_PATH

if __name__ == "__main__":
    generate_youtube_thumbnail()
