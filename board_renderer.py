import os
import math
import chess
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PIECES_DIR = os.path.join(BASE_DIR, "assets", "pieces")

# ---------------------------------------------------------------------------
# Palette: modern dark broadcast theme
# ---------------------------------------------------------------------------
BG_TOP = (11, 15, 22)
BG_BOTTOM = (23, 30, 42)
PANEL = (22, 28, 39)
PANEL_EDGE = (47, 57, 74)
PANEL_DEEP = (15, 19, 27)
TEXT_HI = (241, 245, 251)
TEXT_LO = (146, 160, 180)
GOLD = (232, 184, 66)
GOLD_SOFT = (255, 214, 110)
TEAL = (86, 196, 222)
GREEN_OK = (74, 172, 108)
RED_BAD = (214, 92, 84)
SQ_LIGHT = (235, 238, 220)
SQ_DARK = (116, 148, 88)
HL_YELLOW = (255, 213, 79)
ARROW_GREEN = (21, 120, 27, 210)

PIECE_VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
INITIAL_COUNTS = {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, chess.ROOK: 2, chess.QUEEN: 1}


def find_font(font_type="regular", size=20):
    if font_type == "bold":
        candidates = ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    elif font_type == "mono":
        candidates = ["C:/Windows/Fonts/consolab.ttf", "C:/Windows/Fonts/consola.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"]
    elif font_type == "piece":
        candidates = ["C:/Windows/Fonts/seguisym.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                      "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"]
    else:
        candidates = ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def eval_number(ev):
    s = str(ev).strip()
    if s.startswith('#'):
        return -10.0 if s.startswith('#-') else 10.0
    try:
        return float(s.replace('M', ''))
    except Exception:
        return 0.0


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class ChessBoardRenderer:
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height

        self.brand_font = find_font("bold", 26)
        self.header_font = find_font("regular", 19)
        self.pill_font = find_font("bold", 16)
        self.name_font = find_font("bold", 27)
        self.meta_font = find_font("regular", 18)
        self.clock_font = find_font("mono", 36)
        self.log_head_font = find_font("bold", 17)
        self.log_font = find_font("regular", 19)
        self.log_bold = find_font("bold", 19)
        self.eval_chip_font = find_font("bold", 16)
        self.strat_label_font = find_font("bold", 16)
        self.strat_font = find_font("regular", 20)
        self.sub_font = find_font("regular", 27)
        self.sub_bold = find_font("bold", 20)
        self.coord_font = find_font("bold", 15)
        self.eval_bar_font = find_font("bold", 16)
        self.mat_font = find_font("bold", 18)
        self.big_title_font = find_font("bold", 62)
        self.intro_sub_font = find_font("regular", 28)
        self.intro_small_font = find_font("bold", 22)
        self.glyph_font = find_font("piece", 80)
        self.avatar_glyph = find_font("piece", 46)

        self.sq_size = 104
        self.board_size = self.sq_size * 8
        self.board_x = 1040
        self.board_y = 80
        self.sidebar_x = 48
        self.sidebar_w = 900

        self._bg_cache = None
        self._sprite_cache = {}
        self._glow_cache = None

    # ------------------------------------------------------------------
    # Asset helpers
    # ------------------------------------------------------------------
    def _background(self):
        if self._bg_cache is None:
            col = Image.new("RGB", (1, self.height))
            px = col.load()
            for y in range(self.height):
                px[0, y] = lerp_color(BG_TOP, BG_BOTTOM, y / self.height)
            self._bg_cache = col.resize((self.width, self.height))
        return self._bg_cache.copy()

    def piece_sprite(self, symbol, size=96):
        """symbol like 'wN' / 'bQ'. High-res cburnett PNG, cached per size."""
        key = (symbol, size)
        if key in self._sprite_cache:
            return self._sprite_cache[key]
        path = os.path.join(PIECES_DIR, symbol + ".png")
        sprite = None
        if os.path.exists(path):
            try:
                src = Image.open(path).convert("RGBA")
                sprite = src.resize((size, size), Image.LANCZOS)
            except Exception:
                sprite = None
        if sprite is None:
            sprite = self._glyph_sprite(symbol, size)
        self._sprite_cache[key] = sprite
        return sprite

    def _glyph_sprite(self, symbol, size):
        """Fallback: solid filled glyph with outline stroke (no external assets)."""
        ss = 4
        big = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        filled = {'K': '♚', 'Q': '♛', 'R': '♜', 'B': '♝', 'N': '♞', 'P': '♟'}
        ch = filled.get(symbol[1].upper(), '♟')
        font = find_font("piece", int(size * ss * 0.82))
        is_white = symbol[0] == 'w'
        fill = (250, 250, 250, 255) if is_white else (30, 30, 34, 255)
        stroke = (25, 28, 34, 255) if is_white else (210, 215, 225, 255)
        bbox = d.textbbox((0, 0), ch, font=font, stroke_width=ss)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (size * ss - tw) // 2 - bbox[0]
        y = (size * ss - th) // 2 - bbox[1]
        d.text((x, y), ch, font=font, fill=fill, stroke_width=ss, stroke_fill=stroke)
        return big.resize((size, size), Image.LANCZOS)

    def paste_piece(self, img, symbol, cx, cy, size=96):
        sprite = self.piece_sprite(symbol, size)
        img.paste(sprite, (int(cx - size / 2), int(cy - size / 2)), sprite)

    def square_center(self, sq):
        f, r = chess.square_file(sq), 7 - chess.square_rank(sq)
        return (self.board_x + f * self.sq_size + self.sq_size / 2,
                self.board_y + r * self.sq_size + self.sq_size / 2)

    def _panel(self, draw, box, fill=PANEL, outline=PANEL_EDGE, radius=14, width=2):
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

    def _glow(self, img, box, color, radius=18, spread=8, alpha=70):
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for i in range(spread, 0, -2):
            a = int(alpha * (1 - i / spread) ** 2)
            d.rounded_rectangle([box[0] - i, box[1] - i, box[2] + i, box[3] + i],
                                radius=radius + i, outline=color + (a,), width=2)
        img.alpha_composite(ov)

    # ------------------------------------------------------------------
    # Captured material
    # ------------------------------------------------------------------
    def _captured(self, board, capturer_color):
        enemy = not capturer_color
        counts = {}
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p and p.color == enemy:
                counts[p.piece_type] = counts.get(p.piece_type, 0) + 1
        missing = []
        for pt in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN):
            n = max(0, INITIAL_COUNTS[pt] - counts.get(pt, 0))
            missing.extend([pt] * n)
        return missing

    def _draw_captured_row(self, img, draw, x, y, board, capturer_color):
        missing = self._captured(board, capturer_color)
        prefix = 'b' if capturer_color == chess.WHITE else 'w'
        my_val = sum(PIECE_VALUES[p] for p in missing)
        opp_val = sum(PIECE_VALUES[p] for p in self._captured(board, not capturer_color))
        diff = my_val - opp_val
        if diff > 0:
            label, color = f"+{diff}", GREEN_OK
        elif diff < 0:
            label, color = f"{diff}", RED_BAD
        else:
            label, color = "EVEN", TEXT_LO

        shown = missing[:10]
        label_w = draw.textlength(label, font=self.mat_font)
        chip_w = 12 + len(shown) * 22 + 14 + label_w + 12
        draw.rounded_rectangle([x - 4, y - 3, x - 4 + chip_w, y + 27], radius=9, fill=(28, 35, 48))
        cx = x + 3
        for pt in shown:
            sym = prefix + chess.piece_symbol(pt).upper()
            self.paste_piece(img, sym, cx + 12, y + 12, size=25)
            cx += 22
        draw.text((cx + 12, y + 3), label, font=self.mat_font, fill=color)

    # ------------------------------------------------------------------
    # Player card
    # ------------------------------------------------------------------
    def _player_card(self, img, draw, y, name, meta, clock, active, accent, board, color, glyph_sym):
        x, w, h = self.sidebar_x, self.sidebar_w, 110
        box = [x, y, x + w, y + h]
        if active:
            self._glow(img, box, accent, alpha=90)
        self._panel(draw, box, fill=PANEL, outline=accent if active else PANEL_EDGE,
                    radius=16, width=3 if active else 2)

        av_cx, av_cy, av_r = x + 58, y + h // 2, 38
        draw.ellipse([av_cx - av_r, av_cy - av_r, av_cx + av_r, av_cy + av_r],
                     fill=(32, 40, 54) if color == chess.BLACK else (226, 230, 238),
                     outline=accent if active else PANEL_EDGE, width=3)
        self.paste_piece(img, glyph_sym, av_cx, av_cy, size=54)

        draw.text((x + 116, y + 16), name, font=self.name_font, fill=TEXT_HI)
        draw.text((x + 116, y + 52), meta, font=self.meta_font, fill=TEXT_LO)
        self._draw_captured_row(img, draw, x + 116, y + 78, board, color)

        cw, ch = 158, 66
        cx0, cy0 = x + w - cw - 22, y + (h - ch) // 2
        if active:
            draw.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + ch], radius=10, fill=accent)
            clock_col = (15, 18, 24)
        else:
            draw.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + ch], radius=10,
                                   fill=PANEL_DEEP, outline=PANEL_EDGE, width=2)
            clock_col = TEXT_LO
        tw = draw.textlength(clock, font=self.clock_font)
        draw.text((cx0 + (cw - tw) / 2, cy0 + 13), clock, font=self.clock_font, fill=clock_col)

    # ------------------------------------------------------------------
    # Main frame
    # ------------------------------------------------------------------
    def render_frame(self, board, last_move=None, move_history=None,
                     white_clock="09:45", black_clock="09:50", active_player="White",
                     eval_score=0.0, subtitle_text="", strategy_name="",
                     white_name="White", black_name="Black",
                     white_title="Grandmaster", black_title="Grandmaster",
                     hide_piece_sq=None, show_arrow=True, move_label="",
                     event_name="Grandmaster Classic", progress=None,
                     last_move_san="", subtitle_speaker_name=None,
                     subtitle_accent=None, show_replay_badge=True):
        if move_history is None:
            move_history = []

        img = self._background().convert("RGBA")
        draw = ImageDraw.Draw(img)

        # --- Header ---
        draw.rectangle([0, 0, self.width, 62], fill=(9, 12, 18))
        draw.rectangle([0, 62, self.width, 65], fill=(31, 38, 51))
        if progress is not None:
            p = max(0.0, min(1.0, float(progress)))
            if p > 0:
                draw.rectangle([0, 62, int(self.width * p), 65], fill=GOLD)
        else:
            draw.rectangle([0, 62, self.width, 65], fill=GOLD)
        draw.rounded_rectangle([40, 13, 76, 49], radius=8, fill=GOLD)
        self.paste_piece(img, "bN", 58, 31, size=30)
        draw.text((92, 16), "CHESS MAGIX", font=self.brand_font, fill=TEXT_HI)
        bx = 92 + draw.textlength("CHESS MAGIX", font=self.brand_font) + 24
        if event_name:
            draw.text((bx, 21), "|", font=self.header_font, fill=PANEL_EDGE)
            draw.text((bx + 22, 21), event_name, font=self.header_font, fill=TEXT_LO)

        if move_label:
            tw = draw.textlength(move_label, font=self.pill_font)
            draw.rounded_rectangle([self.width - 60 - tw - 28, 16, self.width - 40, 48],
                                   radius=16, outline=PANEL_EDGE, width=2)
            draw.text((self.width - 60 - tw - 14, 22), move_label, font=self.pill_font, fill=TEXT_LO)
        if show_replay_badge:
            replay = "CLASSIC REPLAY"
            tw = draw.textlength(replay, font=self.pill_font)
            rx = self.width - 60 - tw - 28 - (draw.textlength(move_label, font=self.pill_font) + 42 if move_label else 0) - 16
            draw.rounded_rectangle([rx - tw - 28, 16, rx, 48], radius=16, fill=(20, 42, 40), outline=TEAL, width=2)
            draw.text((rx - tw - 14, 22), replay, font=self.pill_font, fill=TEAL)

        # --- Player cards ---
        self._player_card(img, draw, self.board_y, black_name, black_title, black_clock,
                          active_player == "Black", TEAL, board, chess.BLACK, "bK")
        w_card_y = self.board_y + self.board_size - 110
        self._player_card(img, draw, w_card_y, white_name, white_title, white_clock,
                          active_player == "White", GOLD, board, chess.WHITE, "wK")

        # --- Strategy badge ---
        sy = self.board_y + 122
        self._panel(draw, [self.sidebar_x, sy, self.sidebar_x + self.sidebar_w, sy + 46],
                    fill=PANEL_DEEP, outline=PANEL_EDGE, radius=12, width=2)
        draw.text((self.sidebar_x + 20, sy + 13), "STRATEGY", font=self.strat_label_font, fill=GOLD)
        lx = self.sidebar_x + 20 + draw.textlength("STRATEGY", font=self.strat_label_font) + 22
        strat = strategy_name or "Opening Theory"
        max_w = self.sidebar_x + self.sidebar_w - lx - 20
        while draw.textlength(strat, font=self.strat_font) > max_w and len(strat) > 8:
            strat = strat[:-2]
        if strat != (strategy_name or "Opening Theory"):
            strat = strat.rstrip() + "…"
        draw.text((lx, sy + 11), strat, font=self.strat_font, fill=TEXT_HI)

        # --- Move log ---
        log_y = sy + 58
        log_bottom = w_card_y - 12
        self._panel(draw, [self.sidebar_x, log_y, self.sidebar_x + self.sidebar_w, log_bottom],
                    fill=PANEL_DEEP, outline=PANEL_EDGE, radius=14, width=2)
        draw.rounded_rectangle([self.sidebar_x, log_y, self.sidebar_x + self.sidebar_w, log_y + 42],
                               radius=14, fill=(26, 33, 46))
        draw.rectangle([self.sidebar_x, log_y + 28, self.sidebar_x + self.sidebar_w, log_y + 42], fill=(26, 33, 46))
        cols = (self.sidebar_x + 26, self.sidebar_x + 110, self.sidebar_x + 430, self.sidebar_x + 760)
        draw.text((cols[0], log_y + 11), "#", font=self.log_head_font, fill=TEXT_LO)
        draw.text((cols[1], log_y + 11), "WHITE", font=self.log_head_font, fill=GOLD_SOFT)
        draw.text((cols[2], log_y + 11), "BLACK", font=self.log_head_font, fill=TEAL)
        draw.text((cols[3], log_y + 11), "EVAL", font=self.log_head_font, fill=TEXT_LO)

        if not move_history:
            msg = "THE STAGE IS SET"
            mfont = find_font("bold", 30)
            tw = draw.textlength(msg, font=mfont)
            draw.text((self.sidebar_x + (self.sidebar_w - tw) / 2, log_y + 150),
                      msg, font=mfont, fill=(52, 64, 84))
            msg2 = "The first move is coming up"
            m2 = find_font("regular", 20)
            tw2 = draw.textlength(msg2, font=m2)
            draw.text((self.sidebar_x + (self.sidebar_w - tw2) / 2, log_y + 196),
                      msg2, font=m2, fill=(66, 78, 98))

        row_h = 38
        max_rows = (log_bottom - log_y - 52) // row_h
        visible = move_history[-max_rows:]
        last_idx = len(visible) - 1
        for idx, item in enumerate(visible):
            ry = log_y + 50 + idx * row_h
            is_last = idx == last_idx
            if idx % 2 == 1 and not is_last:
                draw.rectangle([self.sidebar_x + 4, ry - 3, self.sidebar_x + self.sidebar_w - 4, ry + row_h - 5],
                               fill=(20, 26, 36))
            w_txt = item.get('white', '')
            b_txt = item.get('black', '')
            if is_last:
                if b_txt and b_txt != '...':
                    draw.rounded_rectangle([cols[2] - 12, ry - 3, cols[3] - 30, ry + row_h - 5],
                                           radius=8, fill=(38, 52, 66))
                else:
                    draw.rounded_rectangle([cols[1] - 12, ry - 3, cols[2] - 30, ry + row_h - 5],
                                           radius=8, fill=(52, 46, 28))
            draw.text((cols[0], ry + 4), f"{item.get('num', '')}.", font=self.log_font, fill=TEXT_LO)
            draw.text((cols[1], ry + 4), w_txt, font=self.log_bold if is_last else self.log_font, fill=TEXT_HI)
            draw.text((cols[2], ry + 4), b_txt if b_txt != '...' else '…',
                      font=self.log_bold if is_last else self.log_font, fill=TEXT_HI)
            ev = str(item.get('eval', '+0.0'))
            ev_val = eval_number(ev)
            chip_bg = (34, 66, 46) if ev_val > 0.05 else ((66, 36, 34) if ev_val < -0.05 else (40, 46, 58))
            chip_fg = (140, 220, 165) if ev_val > 0.05 else ((235, 150, 140) if ev_val < -0.05 else TEXT_LO)
            draw.rounded_rectangle([cols[3], ry + 2, cols[3] + 92, ry + 30], radius=8, fill=chip_bg)
            ew = draw.textlength(ev, font=self.eval_chip_font)
            draw.text((cols[3] + (92 - ew) / 2, ry + 6), ev, font=self.eval_chip_font, fill=chip_fg)

        # --- Eval bar ---
        self._eval_bar(img, draw, eval_score)

        # --- Board ---
        self._draw_board(img, draw, board, last_move, hide_piece_sq, show_arrow)
        if last_move and last_move_san:
            self._move_tag(img, draw, board, last_move, last_move_san)

        # --- Subtitle banner ---
        self._subtitle_banner(img, draw, subtitle_text, active_player, white_name, black_name,
                              speaker_name=subtitle_speaker_name, accent=subtitle_accent)

        return img.convert("RGB")

    # ------------------------------------------------------------------
    def _eval_bar(self, img, draw, eval_score):
        x, y, w, h = 968, self.board_y, 38, self.board_size
        val = max(-10.0, min(10.0, eval_number(eval_score)))
        white_ratio = 0.5 + 0.5 * math.tanh(val / 6.0)
        split = int(h * (1.0 - white_ratio))

        draw.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=(38, 44, 56))
        if split < h - 4:
            draw.rounded_rectangle([x, y + split, x + w, y + h], radius=8, fill=(242, 244, 248))
            draw.rectangle([x, y + split, x + w, y + split + 10], fill=(242, 244, 248))
        draw.rounded_rectangle([x, y, x + w, y + h], radius=8, outline=PANEL_EDGE, width=2)
        draw.rectangle([x + 5, y + h // 2, x + w - 5, y + h // 2 + 1], fill=(96, 108, 128))
        draw.rectangle([x, y + split - 1, x + w, y + split + 1], fill=GOLD)

        # Board-side advantage tags
        bt = "B"
        wt = "W"
        draw.text((x + (w - draw.textlength(bt, font=self.eval_bar_font)) / 2, y + 7),
                  bt, font=self.eval_bar_font, fill=(205, 214, 228))
        draw.text((x + (w - draw.textlength(wt, font=self.eval_bar_font)) / 2, y + h - 26),
                  wt, font=self.eval_bar_font, fill=(20, 24, 30))

        # Numeric evaluation pinned near the split line
        label = str(eval_score)
        lw = draw.textlength(label, font=self.eval_bar_font)
        chip_w, chip_h = lw + 18, 24
        chip_x = x + (w - chip_w) / 2
        chip_y = max(y + 28, min(y + h - chip_h - 28, y + split - chip_h / 2))
        draw.rounded_rectangle([chip_x, chip_y, chip_x + chip_w, chip_y + chip_h],
                               radius=7, fill=(10, 14, 20), outline=(70, 82, 102), width=1)
        draw.text((chip_x + 9, chip_y + 4), label, font=self.eval_bar_font, fill=TEXT_HI)

    # ------------------------------------------------------------------
    def _draw_board(self, img, draw, board, last_move, hide_piece_sq, show_arrow):
        bx, by, bs = self.board_x, self.board_y, self.board_size
        draw.rounded_rectangle([bx - 18, by - 18, bx + bs + 18, by + bs + 18],
                               radius=12, fill=(26, 32, 44), outline=(52, 62, 80), width=2)

        hl = set()
        if last_move:
            hl = {last_move.from_square, last_move.to_square}
        check_sq = board.king(board.turn) if board.is_check() else None

        for rank in range(8):
            for file in range(8):
                sq = chess.square(file, 7 - rank)
                sx, sy = bx + file * self.sq_size, by + rank * self.sq_size
                is_light = (file + rank) % 2 == 0
                base = SQ_LIGHT if is_light else SQ_DARK
                if sq in hl:
                    base = lerp_color(base, HL_YELLOW, 0.5)
                draw.rectangle([sx, sy, sx + self.sq_size, sy + self.sq_size], fill=base)

                if file == 0:
                    c = SQ_DARK if is_light else SQ_LIGHT
                    if sq in hl:
                        c = lerp_color(c, (120, 100, 20), 0.4)
                    draw.text((sx + 5, sy + 4), str(8 - rank), font=self.coord_font, fill=c)
                if rank == 7:
                    c = SQ_DARK if is_light else SQ_LIGHT
                    if sq in hl:
                        c = lerp_color(c, (120, 100, 20), 0.4)
                    draw.text((sx + self.sq_size - 14, sy + self.sq_size - 21),
                              chr(ord('a') + file), font=self.coord_font, fill=c)

        if check_sq is not None:
            cx, cy = self.square_center(check_sq)
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            r = self.sq_size * 0.62
            for i in range(10, 0, -1):
                rr = r * i / 10
                a = int(150 * (1 - i / 10) ** 1.5) + 20
                od.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(225, 45, 45, a))
            img.alpha_composite(ov)
            draw = ImageDraw.Draw(img)

        for rank in range(8):
            for file in range(8):
                sq = chess.square(file, 7 - rank)
                if sq == hide_piece_sq:
                    continue
                piece = board.piece_at(sq)
                if piece:
                    sym = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()
                    cx, cy = self.square_center(sq)
                    self.paste_piece(img, sym, cx, cy, size=98)

        if last_move and show_arrow:
            self._draw_arrow(img, last_move.from_square, last_move.to_square)

    def _draw_arrow(self, img, start_sq, end_sq):
        ss = 2
        ov = Image.new("RGBA", (self.width * ss, self.height * ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        x1, y1 = self.square_center(start_sq)
        x2, y2 = self.square_center(end_sq)
        x1, y1, x2, y2 = x1 * ss, y1 * ss, x2 * ss, y2 * ss
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        if dist < 8:
            return
        ux, uy = dx / dist, dy / dist
        nx, ny = -uy, ux
        head_len, head_w, shaft_w = 64, 58, 24
        tx, ty = x2 - ux * 30, y2 - uy * 30
        ex, ey = tx - ux * head_len, ty - uy * head_len
        d.line([(x1, y1), (ex, ey)], fill=ARROW_GREEN, width=shaft_w)
        d.polygon([(tx, ty), (ex + nx * head_w / 2, ey + ny * head_w / 2),
                   (ex - nx * head_w / 2, ey - ny * head_w / 2)], fill=ARROW_GREEN)
        ov = ov.resize((self.width, self.height), Image.LANCZOS)
        img.alpha_composite(ov)

    # ------------------------------------------------------------------
    def _move_tag(self, img, draw, board, move, san):
        """Broadcast-style notation pill pinned to the destination square."""
        cx, cy = self.square_center(move.to_square)
        label = f"{san}  CHECKMATE" if board.is_checkmate() else san
        tw = draw.textlength(label, font=self.pill_font)
        w, h = tw + 30, 32
        x0 = cx - w / 2
        y0 = cy - self.sq_size / 2 - h - 8
        if y0 < self.board_y + 4:
            y0 = cy + self.sq_size / 2 + 8
        x0 = max(self.board_x + 6, min(x0, self.board_x + self.board_size - w - 6))
        y0 = max(self.board_y + 4, min(y0, self.board_y + self.board_size - h - 4))
        accent = GOLD_SOFT if board.is_checkmate() else GOLD
        draw.rounded_rectangle([x0 + 2, y0 + 2, x0 + w + 2, y0 + h + 2], radius=10, fill=(6, 9, 14))
        draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=10,
                               fill=(14, 18, 26), outline=accent, width=2)
        draw.text((x0 + 15, y0 + 7), label, font=self.pill_font, fill=accent)
        if board.is_checkmate():
            self._glow(img, [x0, y0, x0 + w, y0 + h], GOLD, radius=10, spread=6, alpha=90)

    # ------------------------------------------------------------------
    def _subtitle_banner(self, img, draw, text, active_player, white_name, black_name,
                         speaker_name=None, accent=None):
        x0, x1 = 48, self.width - 48
        bottom = 1072
        if not text:
            self._panel(draw, [x0, 950, x1, 1054], fill=(14, 18, 26), outline=PANEL_EDGE, radius=16, width=2)
            return
        if accent is None:
            accent = GOLD if (speaker_name is not None or active_player == "White") else TEAL
        if speaker_name is not None:
            speaker = speaker_name
        else:
            speaker = (white_name if active_player == "White" else black_name)
        speaker = speaker.replace("GM ", "").split("&")[0].strip()
        if len(speaker) > 18:
            speaker = speaker.split()[-1]
        sw = draw.textlength(speaker.upper(), font=self.sub_bold)
        chip_w = int(sw) + 36

        # Fixed large font; long phrases wrap to more lines instead of shrinking
        font = self.sub_font
        line_h = 36
        tx = x0 + 24 + chip_w + 26
        max_w = x1 - 32 - tx
        lines = wrap_text(draw, f"“{text}”", font, max_w)
        if len(lines) > 3:
            lines = lines[:3]
            lines[2] = lines[2].rstrip('”') + '…”'
        n = len(lines)
        h = 24 + line_h * n
        y = bottom - h
        self._panel(draw, [x0, y, x1, bottom], fill=(14, 18, 26), outline=PANEL_EDGE, radius=16, width=2)
        chip_y = y + (h - 36) // 2
        draw.rounded_rectangle([x0 + 24, chip_y, x0 + 24 + chip_w, chip_y + 36], radius=10, fill=accent)
        draw.text((x0 + 42, chip_y + 6), speaker.upper(), font=self.sub_bold, fill=(15, 18, 24))
        ty = y + 12
        for ln in lines:
            draw.text((tx, ty), ln, font=font, fill=TEXT_HI)
            ty += line_h

    # ------------------------------------------------------------------
    # Intro / outro cards
    # ------------------------------------------------------------------
    def render_intro(self, game_info):
        img = self._background().convert("RGBA")
        draw = ImageDraw.Draw(img)
        cx = self.width // 2

        draw.rectangle([0, 0, self.width, 6], fill=GOLD)
        tag = "CHESS MAGIX  PRESENTS"
        tw = draw.textlength(tag, font=self.intro_small_font)
        draw.text((cx - tw / 2, 120), tag, font=self.intro_small_font, fill=GOLD)

        white = game_info.get("white_name", "White").replace("GM ", "")
        black = game_info.get("black_name", "Black").replace("GM ", "")
        title = f"{white}  vs  {black}"
        font = self.big_title_font
        while draw.textlength(title, font=font) > self.width - 200 and font.size > 34:
            font = find_font("bold", font.size - 4)
        tw = draw.textlength(title, font=font)
        draw.text((cx - tw / 2, 200), title, font=font, fill=TEXT_HI)

        event = game_info.get("event", "Grandmaster Classic")
        opening = game_info.get("opening", "")
        sub = f"{event}   •   {opening}" if opening else event
        tw = draw.textlength(sub, font=self.intro_sub_font)
        draw.text((cx - tw / 2, 310), sub, font=self.intro_sub_font, fill=TEXT_LO)

        theme = game_info.get("theme", "")
        if theme:
            tw = draw.textlength(theme, font=self.intro_sub_font)
            if tw > self.width - 300:
                theme = theme[:80] + "…"
                tw = draw.textlength(theme, font=self.intro_sub_font)
            draw.text((cx - tw / 2, 360), theme, font=self.intro_sub_font, fill=TEAL)

        card_w, card_h, gap = 560, 240, 80
        total = card_w * 2 + gap
        x0 = cx - total // 2
        y0 = 480
        for i, (name, rating, sym, accent) in enumerate([
            (game_info.get("white_name", "White"), game_info.get("white_rating", "2800"), "wK", GOLD),
            (game_info.get("black_name", "Black"), game_info.get("black_rating", "2800"), "bK", TEAL),
        ]):
            x = x0 + i * (card_w + gap)
            self._panel(draw, [x, y0, x + card_w, y0 + card_h], fill=PANEL, outline=accent, radius=20, width=3)
            av_cx, av_cy = x + 100, y0 + card_h // 2
            draw.ellipse([av_cx - 56, av_cy - 56, av_cx + 56, av_cy + 56],
                         fill=(226, 230, 238) if i == 0 else (32, 40, 54), outline=accent, width=3)
            self.paste_piece(img, sym, av_cx, av_cy, size=80)
            nm = name.replace("GM ", "")
            nfont = find_font("bold", 30)
            while draw.textlength(nm, font=nfont) > card_w - 200 and nfont.size > 20:
                nfont = find_font("bold", nfont.size - 2)
            draw.text((x + 185, y0 + 78), nm, font=nfont, fill=TEXT_HI)
            draw.text((x + 185, y0 + 128), f"Rating {rating}", font=self.intro_sub_font, fill=TEXT_LO)
            side = "WHITE" if i == 0 else "BLACK"
            draw.text((x + 185, y0 + 170), side, font=self.intro_small_font, fill=accent)

        vs = "VS"
        vfont = find_font("bold", 44)
        tw = draw.textlength(vs, font=vfont)
        draw.text((cx - tw / 2, y0 + card_h // 2 - 30), vs, font=vfont, fill=GOLD)

        badge = game_info.get("climax_badge", "")
        if badge:
            bfont = find_font("bold", 24)
            bw = draw.textlength(badge, font=bfont)
            draw.rounded_rectangle([cx - bw / 2 - 24, 728, cx + bw / 2 + 24, 776],
                                   radius=24, fill=(48, 38, 18), outline=GOLD, width=2)
            draw.text((cx - bw / 2, 740), badge, font=bfont, fill=GOLD_SOFT)

        hook = game_info.get("climax_hook", "A LEGENDARY BATTLE")
        hfont = find_font("bold", 34)
        while draw.textlength(hook, font=hfont) > self.width - 240 and hfont.size > 22:
            hfont = find_font("bold", hfont.size - 2)
        tw = draw.textlength(hook, font=hfont)
        draw.text((cx - tw / 2, 810), hook, font=hfont, fill=GOLD_SOFT)

        pill = "WATCH TILL THE END  •  SUBSCRIBE"
        tw = draw.textlength(pill, font=self.intro_small_font)
        draw.rounded_rectangle([cx - tw / 2 - 30, 900, cx + tw / 2 + 30, 952], radius=26,
                               outline=GOLD, width=2)
        draw.text((cx - tw / 2, 914), pill, font=self.intro_small_font, fill=GOLD)
        return img.convert("RGB")

    def render_outro(self, game_info, result_text="1-0", summary=""):
        img = self._background().convert("RGBA")
        draw = ImageDraw.Draw(img)
        cx = self.width // 2
        draw.rectangle([0, 0, self.width, 6], fill=GOLD)

        tag = "FINAL RESULT"
        tw = draw.textlength(tag, font=self.intro_small_font)
        draw.text((cx - tw / 2, 150), tag, font=self.intro_small_font, fill=TEXT_LO)

        rfont = find_font("bold", 130)
        tw = draw.textlength(result_text, font=rfont)
        draw.text((cx - tw / 2, 210), result_text, font=rfont, fill=GOLD)

        if summary:
            sfont = find_font("bold", 40)
            while draw.textlength(summary, font=sfont) > self.width - 240 and sfont.size > 24:
                sfont = find_font("bold", sfont.size - 2)
            tw = draw.textlength(summary, font=sfont)
            draw.text((cx - tw / 2, 400), summary, font=sfont, fill=TEXT_HI)

        white = game_info.get("white_name", "White")
        black = game_info.get("black_name", "Black")
        line = f"{white}  vs  {black}  •  {game_info.get('event', '')}"
        tw = draw.textlength(line, font=self.intro_sub_font)
        draw.text((cx - tw / 2, 490), line, font=self.intro_sub_font, fill=TEXT_LO)

        self.paste_piece(img, "wK", cx - 120, 650, size=110)
        self.paste_piece(img, "bK", cx + 120, 650, size=110)

        note = "COMMENT YOUR FAVORITE MOVE BELOW"
        tw = draw.textlength(note, font=self.meta_font)
        draw.text((cx - tw / 2, 724), note, font=self.meta_font, fill=TEXT_LO)

        cta = "SUBSCRIBE  •  NEW GAME EVERY DAY"
        tw = draw.textlength(cta, font=self.intro_small_font)
        draw.rounded_rectangle([cx - tw / 2 - 36, 780, cx + tw / 2 + 36, 840], radius=30, fill=GOLD)
        draw.text((cx - tw / 2, 797), cta, font=self.intro_small_font, fill=(15, 18, 24))

        brand = "CHESS MAGIX"
        tw = draw.textlength(brand, font=self.brand_font)
        draw.text((cx - tw / 2, 900), brand, font=self.brand_font, fill=TEXT_LO)
        return img.convert("RGB")