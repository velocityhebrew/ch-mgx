"""
Vertical YouTube Shorts generator.

Creates 9:16 highlights from the same game as the long-form video:
  - climax:  can you find the winning move?
  - finish:  how did this game end?
  - opening: can you spot the opening trap?

The daily runner uploads one long video and up to three Shorts, scheduled
across the day.
"""

import os
import io
import asyncio
import subprocess

import chess
import chess.pgn
from PIL import Image, ImageDraw

from board_renderer import (
    ChessBoardRenderer, find_font, wrap_text, lerp_color,
    BG_TOP, BG_BOTTOM, PANEL, PANEL_EDGE, PANEL_DEEP,
    TEXT_HI, TEXT_LO, GOLD, GOLD_SOFT, TEAL, GREEN_OK, RED_BAD,
)
from match_narrator import ChessNarrator
from grandmaster_database import parse_game_moves
from generate_chess_video import (
    encode_still_segment, encode_move_segment, probe_duration,
    spoken_eval, format_srt_time, ANIM_FRAMES, FPS,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
FRAMES_DIR = os.path.join(RECORDINGS_DIR, "frames")
VOICE_DIR = os.path.join(BASE_DIR, "voiceover")
os.makedirs(FRAMES_DIR, exist_ok=True)

MOMENT_CONFIG = {
    "climax": {
        "hook": "CAN YOU FIND THE WINNING MOVE?",
        "hook_spoken": "Can you find the winning move?",
        "title": "Can You Find the Winning Move?",
        "cta": "FULL GAME ON CHESS MAGIX",
        "reveal_prefix": "The move is",
        "reveal_tail": "finds it, and the evaluation jumps to {eval}.",
    },
    "finish": {
        "hook": "HOW DID THIS GAME END?",
        "hook_spoken": "How did this game end?",
        "title": "How Did This Game End?",
        "cta": "WATCH THE FULL GAME",
        "reveal_prefix": "The final move is",
        "reveal_tail": "finishes it.",
    },
    "opening": {
        "hook": "CAN YOU SPOT THE OPENING TRAP?",
        "hook_spoken": "Can you spot the opening trap?",
        "title": "Can You Spot the Opening Trap?",
        "cta": "FULL GAME ON CHESS MAGIX",
        "reveal_prefix": "The trap is",
        "reveal_tail": "strikes early.",
    },
}


def short_paths(suffix):
    return {
        "video": os.path.join(RECORDINGS_DIR, f"short_{suffix}.mp4"),
        "srt": os.path.join(RECORDINGS_DIR, f"short_{suffix}.srt"),
        "thumb": os.path.join(RECORDINGS_DIR, f"short_{suffix}_thumbnail.png"),
    }


def spoken_move(san):
    if san == "O-O":
        return "castles kingside"
    if san == "O-O-O":
        return "castles queenside"
    return san.replace("#", " checkmate").replace("+", " check").replace("x", " takes ")


def apply_move(board, history, move_data, ply):
    player = move_data["player"]
    san_display = move_data["san"] + move_data.get("note", "")
    ev = move_data["eval"]
    board.push(chess.Move.from_uci(move_data["move"]))
    move_num = (ply + 1) // 2
    if player == "White":
        history.append({"num": move_num, "white": san_display, "black": "...", "eval": ev})
    elif history:
        history[-1]["black"] = san_display
        history[-1]["eval"] = ev


class ShortsRenderer:
    """1080x1920 broadcast layout for Shorts."""

    def __init__(self):
        self.width, self.height = 1080, 1920
        self.base = ChessBoardRenderer()
        self.board_x, self.board_y, self.board_size = 60, 400, 960
        self.crop_box = (1022, 62, 1890, 930)
        self.crop_size = self.crop_box[2] - self.crop_box[0]
        self.scale = self.board_size / self.crop_size

        self.brand_font = find_font("bold", 38)
        self.pill_font = find_font("bold", 20)
        self.hook_font = find_font("bold", 56)
        self.name_font = find_font("bold", 32)
        self.rating_font = find_font("regular", 24)
        self.move_font = find_font("bold", 30)
        self.sub_font = find_font("regular", 32)
        self.cta_font = find_font("bold", 30)
        self.small_font = find_font("bold", 20)
        self._bg = None

    def _background(self):
        if self._bg is None:
            col = Image.new("RGB", (1, self.height))
            px = col.load()
            for y in range(self.height):
                px[0, y] = lerp_color(BG_TOP, BG_BOTTOM, y / self.height)
            self._bg = col.resize((self.width, self.height))
        return self._bg.copy()

    def board_image(self, board, last_move=None, last_move_san="", history=None,
                    hide_piece_sq=None, show_arrow=True, progress=0.8):
        frame = self.base.render_frame(
            board, last_move=last_move, move_history=history or [],
            white_clock="10:00", black_clock="10:00", active_player="White",
            eval_score=0.0, subtitle_text="", strategy_name="",
            white_name="White", black_name="Black",
            white_title="Grandmaster", black_title="Grandmaster",
            move_label="", event_name="", progress=progress,
            last_move_san=last_move_san, show_replay_badge=False,
            hide_piece_sq=hide_piece_sq, show_arrow=show_arrow,
        )
        return frame.crop(self.crop_box).resize(
            (self.board_size, self.board_size), Image.LANCZOS
        )

    def _header(self, img, draw):
        draw.rectangle([0, 0, self.width, 6], fill=GOLD)
        draw.rounded_rectangle([40, 32, 98, 90], radius=12, fill=GOLD)
        self.base.paste_piece(img, "bN", 69, 61, size=42)
        draw.text((116, 42), "CHESS MAGIX", font=self.brand_font, fill=TEXT_HI)
        tw = draw.textlength("SHORTS", font=self.pill_font)
        draw.rounded_rectangle([self.width - 60 - tw - 36, 42, self.width - 40, 82],
                               radius=16, fill=(200, 30, 45))
        draw.text((self.width - 60 - tw - 18, 50), "SHORTS", font=self.pill_font, fill=(255, 255, 255))

    def _hook(self, draw, text):
        font = self.hook_font
        lines = wrap_text(draw, text, font, 960)
        while len(lines) > 2 and font.size > 40:
            font = find_font("bold", font.size - 4)
            lines = wrap_text(draw, text, font, 960)
        if len(lines) > 2:
            lines = lines[:2]
            lines[1] = lines[1].rstrip("?!") + "?!"
        line_h = int(font.size * 1.1)
        total = line_h * len(lines)
        y = 130 + (110 - total) // 2
        for line in lines:
            tw = draw.textlength(line, font=font)
            draw.text(((self.width - tw) / 2, y), line, font=font,
                      fill=GOLD_SOFT, stroke_width=2, stroke_fill=(40, 30, 8))
            y += line_h

    def _players(self, draw, white, black, white_rating, black_rating):
        names = f"{white}  vs  {black}"
        font = self.name_font
        while draw.textlength(names, font=font) > 960 and font.size > 22:
            font = find_font("bold", font.size - 2)
        tw = draw.textlength(names, font=font)
        draw.text(((self.width - tw) / 2, 292), names, font=font, fill=TEXT_HI)
        ratings = f"{white_rating}   •   {black_rating}"
        tw = draw.textlength(ratings, font=self.rating_font)
        draw.text(((self.width - tw) / 2, 338), ratings, font=self.rating_font, fill=TEXT_LO)

    def _move_panel(self, draw, move_label, badge, eval_score):
        draw.rounded_rectangle([40, 1380, 1040, 1452], radius=16, fill=PANEL_DEEP,
                               outline=PANEL_EDGE, width=2)
        label = f"{move_label}   {badge}"
        font = self.move_font
        while draw.textlength(label, font=font) > 760 and font.size > 20:
            font = find_font("bold", font.size - 2)
        draw.text((64, 1398), label, font=font, fill=TEXT_HI)

        ev = str(eval_score)
        tw = draw.textlength(ev, font=self.move_font)
        chip_w = tw + 28
        if ev == "?":
            chip_fill, chip_fg = (40, 46, 58), TEXT_LO
        else:
            chip_fill, chip_fg = (34, 66, 46), (150, 225, 178)
        draw.rounded_rectangle([1020 - chip_w, 1398, 1020, 1434], radius=9,
                               fill=chip_fill)
        draw.text((1020 - chip_w + 14, 1403), ev, font=self.move_font, fill=chip_fg)

    def _subtitle(self, draw, text):
        draw.rounded_rectangle([40, 1470, 1040, 1600], radius=16, fill=(14, 18, 26),
                               outline=PANEL_EDGE, width=2)
        chip = "CHESS MAGIX"
        cw = draw.textlength(chip, font=self.small_font) + 28
        draw.rounded_rectangle([64, 1490, 64 + cw, 1528], radius=10, fill=GOLD)
        draw.text((80, 1496), chip, font=self.small_font, fill=(15, 18, 24))

        font = self.sub_font
        tx = 64 + cw + 22
        lines = wrap_text(draw, text, font, 1040 - 40 - tx)
        while len(lines) > 3 and font.size > 24:
            font = find_font("regular", font.size - 2)
            lines = wrap_text(draw, text, font, 1040 - 40 - tx)
        if len(lines) > 3:
            lines = lines[:3]
            lines[2] = lines[2].rstrip(".") + "…"
        line_h = int(font.size * 1.25)
        ty = 1488
        for line in lines:
            draw.text((tx, ty), line, font=font, fill=TEXT_HI)
            ty += line_h

    def _cta(self, draw, text):
        font = self.cta_font
        while draw.textlength(text, font=font) > 700 and font.size > 20:
            font = find_font("bold", font.size - 2)
        tw = draw.textlength(text, font=font)
        draw.rounded_rectangle([(self.width - tw) / 2 - 40, 1630, (self.width + tw) / 2 + 40, 1702],
                               radius=36, fill=GOLD)
        draw.text(((self.width - tw) / 2, 1648), text, font=font, fill=(15, 18, 24))

    def render(self, board, last_move=None, last_move_san="", history=None,
               hide_piece_sq=None, show_arrow=True, hook="", white="White",
               black="Black", white_rating="2800", black_rating="2800",
               move_label="", badge="", eval_score=0.0, subtitle="",
               cta="FULL GAME ON CHESS MAGIX", progress=0.8):
        img = self._background().convert("RGBA")
        draw = ImageDraw.Draw(img)
        self._header(img, draw)
        self._hook(draw, hook)
        self._players(draw, white, black, white_rating, black_rating)

        board_img = self.board_image(
            board, last_move=last_move, last_move_san=last_move_san,
            history=history, hide_piece_sq=hide_piece_sq,
            show_arrow=show_arrow, progress=progress,
        )
        img.paste(board_img, (self.board_x, self.board_y))
        draw.rectangle([self.board_x - 2, self.board_y - 2,
                        self.board_x + self.board_size + 2, self.board_y + self.board_size + 2],
                       outline=GOLD, width=3)

        self._move_panel(draw, move_label, badge, eval_score)
        self._subtitle(draw, subtitle)
        self._cta(draw, cta)
        return img.convert("RGB")


def _write_srt(entries, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(entries, 1):
            f.write(f"{i}\n{format_srt_time(start)} --> {format_srt_time(end)}\n{text}\n\n")


def _find_opening_ply(moves, climax_ply, finish_ply):
    """Pick a real early tactic: a check, queen raid, or promotion."""
    if len(moves) < 12:
        return None
    limit = min(30, max(12, int(len(moves) * 0.4)))
    best = None
    for ply, move_data in enumerate(moves[:limit], 1):
        if ply in (climax_ply, finish_ply):
            continue
        san = move_data["san"]
        score = 0
        if "#" in san:
            score += 50
        elif "+" in san:
            score += 10
        if san.startswith("Qx"):
            score += 12
        elif "x" in san:
            score += 2
        if "=" in san:
            score += 10
        if score >= 10 and (best is None or score > best[0]):
            best = (score, ply)
    return best[1] if best else None


def _moment_plan(game_info, moves):
    climax_ply = int(game_info.get("climax_ply") or len(moves))
    climax_ply = max(1, min(climax_ply, len(moves)))
    plan = [("climax", climax_ply)]
    finish_ply = len(moves)
    if finish_ply != climax_ply:
        plan.append(("finish", finish_ply))
    opening_ply = _find_opening_ply(moves, climax_ply, finish_ply)
    if opening_ply:
        plan.append(("opening", opening_ply))
    return plan[:3]


def _badge_for(moment, game_info, san, captured):
    if moment == "climax":
        return game_info.get("climax_badge", "!! TACTICAL BLOW")
    if "#" in san:
        return "!! CHECKMATE"
    if moment == "finish":
        if captured is not None:
            return "!! FINAL CAPTURE"
        if "+" in san:
            return "!! FINAL CHECK"
        return "!! FINAL BLOW"
    if captured is not None and captured.piece_type == chess.QUEEN:
        return "!! QUEEN RAID"
    if "#" in san:
        return "!! EARLY MATE"
    if "+" in san:
        return "!! EARLY CHECK"
    if "=" in san:
        return "!! EARLY PROMOTION"
    return "!! EARLY TACTIC"


async def generate_short(game_info, moment="climax", custom_ply=None, suffix=None):
    """Generate one vertical Short for the requested moment."""
    moves = parse_game_moves(game_info)
    if not moves:
        raise RuntimeError("No moves to build a Short from")

    climax_ply = int(game_info.get("climax_ply") or len(moves))
    climax_ply = max(1, min(climax_ply, len(moves)))
    ply = custom_ply or (len(moves) if moment == "finish" else climax_ply)
    ply = max(1, min(ply, len(moves)))
    suffix = suffix or moment
    config = MOMENT_CONFIG[moment]
    paths = short_paths(suffix)

    move_data = moves[ply - 1]
    last_move = chess.Move.from_uci(move_data["move"])
    san = move_data["san"]
    san_display = san + move_data.get("note", "")
    eval_score = move_data["eval"]
    player = move_data["player"]

    board_before = chess.Board()
    history_before = []
    for idx, md in enumerate(moves[:ply - 1], 1):
        apply_move(board_before, history_before, md, idx)

    board_after = board_before.copy()
    history_after = [dict(h) for h in history_before]
    apply_move(board_after, history_after, move_data, ply)

    captured = board_before.piece_at(last_move.to_square)
    badge = _badge_for(moment, game_info, san, captured)
    move_num = (ply + 1) // 2

    white = game_info.get("white_name", "White")
    black = game_info.get("black_name", "Black")
    white_clean = white.replace("GM ", "")
    black_clean = black.replace("GM ", "")
    white_rating = game_info.get("white_rating", "2800")
    black_rating = game_info.get("black_rating", "2800")
    pgn = game_info.get("pgn", "")
    if "1-0" in pgn:
        result = "WHITE WINS"
    elif "0-1" in pgn:
        result = "BLACK WINS"
    else:
        result = "DRAW"

    narrator = ChessNarrator(VOICE_DIR)
    badge_spoken = str(badge).lstrip("! ").strip().lower()
    player_clean = white_clean if player == "White" else black_clean

    hook_text = f"{config['hook_spoken']} {white_clean} versus {black_clean}."
    if moment == "climax":
        reveal_text = (
            f"The move is {spoken_move(san)}. {badge_spoken}. "
            f"{player_clean} finds it, and the evaluation jumps to {spoken_eval(eval_score)}."
        )
    else:
        move_phrase = spoken_move(san)
        duplicate_check = (
            badge_spoken and (
                badge_spoken in move_phrase
                or ("check" in badge_spoken and "check" in move_phrase)
            )
        )
        if duplicate_check:
            badge_clause = ""
        else:
            badge_clause = f"{badge_spoken}. "
        reveal_text = (
            f"{config['reveal_prefix']} {move_phrase}. {badge_clause}"
            f"{player_clean} {config['reveal_tail']}"
        )
    cta_text = "Full game on Chess Magix. Subscribe for daily grandmaster battles."

    hook_audio = await narrator.generate_dialogue(f"short_{suffix}_hook", "Host", hook_text)
    reveal_audio = await narrator.generate_dialogue(f"short_{suffix}_reveal", "Host", reveal_text)
    cta_audio = await narrator.generate_dialogue(f"short_{suffix}_cta", "Host", cta_text)

    hook_dur = narrator.get_audio_duration(hook_audio) + 0.6
    reveal_dur = narrator.get_audio_duration(reveal_audio) + 0.6
    cta_dur = narrator.get_audio_duration(cta_audio) + 0.6

    renderer = ShortsRenderer()
    base_kwargs = dict(
        white=white_clean, black=black_clean,
        white_rating=white_rating, black_rating=black_rating,
        progress=ply / max(1, len(moves)),
    )

    hook_img = renderer.render(
        board_before, last_move=None, last_move_san="", history=history_before,
        show_arrow=False, hook=config["hook"],
        subtitle=config["hook_spoken"], cta=config["cta"],
        move_label=f"MOVE {move_num}", badge="FIND THE MOVE", eval_score="?",
        **base_kwargs,
    )
    reveal_img = renderer.render(
        board_after, last_move=last_move, last_move_san=san_display, history=history_after,
        show_arrow=True, hook=f"THE MOVE: {san_display}", subtitle=reveal_text,
        cta=config["cta"], move_label=f"MOVE {move_num}",
        badge=badge, eval_score=eval_score, **base_kwargs,
    )
    cta_img = renderer.render(
        board_after, last_move=last_move, last_move_san=san_display, history=history_after,
        show_arrow=True, hook=result, subtitle=cta_text,
        cta=config["cta"], move_label=f"MOVE {move_num}",
        badge=badge, eval_score=eval_score, **base_kwargs,
    )

    hook_frame = os.path.join(FRAMES_DIR, f"short_{suffix}_hook.png")
    reveal_frame = os.path.join(FRAMES_DIR, f"short_{suffix}_reveal.png")
    cta_frame = os.path.join(FRAMES_DIR, f"short_{suffix}_cta.png")
    hook_img.save(hook_frame)
    reveal_img.save(reveal_frame)
    cta_img.save(cta_frame)
    reveal_img.save(paths["thumb"])

    seg_hook = os.path.join(RECORDINGS_DIR, f"short_{suffix}_seg_hook.mp4")
    seg_reveal = os.path.join(RECORDINGS_DIR, f"short_{suffix}_seg_reveal.mp4")
    seg_cta = os.path.join(RECORDINGS_DIR, f"short_{suffix}_seg_cta.mp4")

    encode_still_segment(hook_frame, hook_audio, hook_dur, seg_hook)

    anim_base = renderer.render(
        board_after, last_move=None, last_move_san="", history=history_after,
        hide_piece_sq=last_move.to_square, show_arrow=False,
        hook=f"THE MOVE: {san_display}", subtitle=reveal_text,
        cta=config["cta"], move_label=f"MOVE {move_num}",
        badge=badge, eval_score=eval_score, **base_kwargs,
    )
    piece_sym = ("w" if player == "White" else "b") + board_after.piece_at(last_move.to_square).symbol().upper()
    x1b, y1b = renderer.base.square_center(last_move.from_square)
    x2b, y2b = renderer.base.square_center(last_move.to_square)
    scale = renderer.scale
    x1 = (x1b - renderer.crop_box[0]) * scale + renderer.board_x
    y1 = (y1b - renderer.crop_box[1]) * scale + renderer.board_y
    x2 = (x2b - renderer.crop_box[0]) * scale + renderer.board_x
    y2 = (y2b - renderer.crop_box[1]) * scale + renderer.board_y
    piece_size = int(98 * scale)

    for k in range(ANIM_FRAMES):
        t = (k + 1) / ANIM_FRAMES
        ease = 1 - (1 - t) ** 3
        cx = x1 + (x2 - x1) * ease
        cy = y1 + (y2 - y1) * ease
        frame = anim_base.copy()
        renderer.base.paste_piece(frame, piece_sym, cx, cy, size=piece_size)
        frame.save(os.path.join(FRAMES_DIR, f"short_{suffix}_anim_{k:02d}.png"))

    anim_pattern = os.path.join(FRAMES_DIR, f"short_{suffix}_anim_%02d.png")
    encode_move_segment(anim_pattern, reveal_frame, reveal_audio, reveal_dur, seg_reveal)
    encode_still_segment(cta_frame, cta_audio, cta_dur, seg_cta)

    concat_file = os.path.join(RECORDINGS_DIR, f"short_{suffix}_concat.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for seg in (seg_hook, seg_reveal, seg_cta):
            f.write(f"file '{os.path.basename(seg)}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
           "-c", "copy", "-movflags", "+faststart", paths["video"]]
    res = subprocess.run(cmd, cwd=RECORDINGS_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise RuntimeError(f"Short concat failed: {res.stderr.decode()[-800:]}")

    duration = probe_duration(paths["video"])
    if duration is None:
        raise RuntimeError("Could not read Short duration")
    if duration > 60:
        raise RuntimeError(f"Short is too long: {duration:.1f}s (limit 60s)")

    _write_srt([
        (0.0, hook_dur, hook_text),
        (hook_dur, hook_dur + reveal_dur, reveal_text),
        (hook_dur + reveal_dur, hook_dur + reveal_dur + cta_dur, cta_text),
    ], paths["srt"])

    title = f"{config['title']} {white_clean} vs {black_clean}"
    hook_line = f"{white_clean} vs {black_clean}: {config['hook_spoken'].lower()}"
    print(f"[short:{moment}] Generated {duration:.1f}s Short: {paths['video']}")
    return {
        "path": paths["video"],
        "thumbnail": paths["thumb"],
        "srt": paths["srt"],
        "duration": duration,
        "title": title,
        "hook": hook_line,
        "moment": moment,
        "description": f"#Shorts\n{hook_line}\n\n#Chess #Grandmaster #ChessMagix",
    }


async def generate_all_shorts(game_info):
    """Generate the climax, finish, and opening-trap Shorts (up to 3)."""
    moves = parse_game_moves(game_info)
    plan = _moment_plan(game_info, moves)
    results = []
    for moment, ply in plan:
        try:
            info = await generate_short(game_info, moment=moment, custom_ply=ply, suffix=moment)
            results.append(info)
        except Exception as e:
            print(f"[short:{moment}] Generation failed: {e}")
    return results


if __name__ == "__main__":
    from grandmaster_database import get_game_of_the_day
    infos = asyncio.run(generate_all_shorts(get_game_of_the_day("reti_tartakower_1910")))
    for info in infos:
        print(info)
