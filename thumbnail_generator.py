import os
import chess
from PIL import Image, ImageDraw, ImageFont
from board_renderer import ChessBoardRenderer
from grandmaster_database import get_kasparov_game_moves

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
THUMBNAIL_PATH = os.path.join(RECORDINGS_DIR, "thumbnail.png")

BOLD_FONT = "C:/Windows/Fonts/segoeuib.ttf"
TITLE_FONT = "C:/Windows/Fonts/impact.ttf"

def generate_youtube_thumbnail():
    print("[*] Generating high-CTR YouTube thumbnail at mid-game climax...")
    renderer = ChessBoardRenderer()

    moves = get_kasparov_game_moves()
    climax_ply = 47 # Move 24: Rxd4!!
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

    last_move = chess.Move.from_uci(moves[climax_ply - 1]["move"])
    
    frame = renderer.render_frame(
        board=board,
        last_move=last_move,
        move_history=history[-12:],
        white_clock="06:12",
        black_clock="06:34",
        active_player="White",
        eval_score="+3.5",
        subtitle_text="Rook takes d4!! An immortal piece sacrifice! Shattering Black's king shelter!",
        strategy_name="!! THE IMMORTAL ROOK SACRIFICE (Rxd4!!)"
    )

    draw = ImageDraw.Draw(frame)

    try:
        impact_big = ImageFont.truetype(TITLE_FONT, 56)
        impact_sub = ImageFont.truetype(BOLD_FONT, 28)
        badge_font = ImageFont.truetype(BOLD_FONT, 34)
    except Exception:
        impact_big = ImageFont.load_default()
        impact_sub = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    # Top YouTube Hook Banner
    draw.rectangle([940, 15, 1772, 60], fill=(220, 20, 60))
    draw.text((960, 18), "STOCKFISH 19 (3600+ ELO) IMMORTAL BATTLE", font=impact_sub, fill=(255, 255, 255))

    # Climax Badge on Board
    badge_x, badge_y = 960, 85
    draw.rectangle([badge_x, badge_y, badge_x + 390, badge_y + 60], fill=(0, 200, 255), outline=(255, 255, 255), width=3)
    draw.text((badge_x + 18, badge_y + 10), "!! IMMORTAL SACRIFICE", font=badge_font, fill=(0, 0, 0))

    # Bottom Callout Banner
    callout_y = 860
    draw.rectangle([940, callout_y, 1772, callout_y + 55], fill=(218, 165, 32), outline=(255, 255, 255), width=2)
    draw.text((960, callout_y + 10), "GREATEST ROOK SACRIFICE IN HISTORY?!", font=impact_sub, fill=(0, 0, 0))

    frame.save(THUMBNAIL_PATH)
    print(f"[SUCCESS] YouTube thumbnail generated at: {THUMBNAIL_PATH}")
    return THUMBNAIL_PATH

if __name__ == "__main__":
    generate_youtube_thumbnail()
