import os
import math
import chess
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "C:/Windows/Fonts/seguisym.ttf"
BOLD_FONT_PATH = "C:/Windows/Fonts/segoeuib.ttf"
REG_FONT_PATH = "C:/Windows/Fonts/segoeui.ttf"

# Unicode piece mapping
PIECE_GLYPHS = {
    'K': '\u2654', 'Q': '\u2655', 'R': '\u2656', 'B': '\u2657', 'N': '\u2658', 'P': '\u2659',
    'k': '\u265A', 'q': '\u265B', 'r': '\u265C', 'b': '\u265D', 'n': '\u265E', 'p': '\u265F',
}

class ChessBoardRenderer:
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        
        # Load fonts
        try:
            self.piece_font = ImageFont.truetype(FONT_PATH, 74)
            self.avatar_font = ImageFont.truetype(FONT_PATH, 42)
            self.title_font = ImageFont.truetype(BOLD_FONT_PATH, 22)
            self.player_font = ImageFont.truetype(BOLD_FONT_PATH, 20)
            self.clock_font = ImageFont.truetype(BOLD_FONT_PATH, 26)
            self.log_font = ImageFont.truetype(REG_FONT_PATH, 17)
            self.log_bold = ImageFont.truetype(BOLD_FONT_PATH, 17)
            self.sub_font = ImageFont.truetype(REG_FONT_PATH, 21)
            self.sub_bold = ImageFont.truetype(BOLD_FONT_PATH, 21)
            self.coord_font = ImageFont.truetype(BOLD_FONT_PATH, 15)
            self.badge_font = ImageFont.truetype(BOLD_FONT_PATH, 13)
        except Exception:
            self.piece_font = ImageFont.load_default()
            self.avatar_font = ImageFont.load_default()
            self.title_font = ImageFont.load_default()
            self.player_font = ImageFont.load_default()
            self.clock_font = ImageFont.load_default()
            self.log_font = ImageFont.load_default()
            self.log_bold = ImageFont.load_default()
            self.sub_font = ImageFont.load_default()
            self.sub_bold = ImageFont.load_default()
            self.coord_font = ImageFont.load_default()
            self.badge_font = ImageFont.load_default()

        # Board layout dimensions
        self.sq_size = 104
        self.board_size = self.sq_size * 8  # 832x832
        self.board_x = 940
        self.board_y = 65

    def draw_arrow(self, draw: ImageDraw.ImageDraw, start_sq: int, end_sq: int, color=(235, 65, 65, 230), width=12):
        """Draws a clean, anti-aliased tactical arrow between two squares."""
        x1_file, y1_rank = chess.square_file(start_sq), 7 - chess.square_rank(start_sq)
        x2_file, y2_rank = chess.square_file(end_sq), 7 - chess.square_rank(end_sq)

        p1_x = self.board_x + x1_file * self.sq_size + self.sq_size // 2
        p1_y = self.board_y + y1_rank * self.sq_size + self.sq_size // 2
        p2_x = self.board_x + x2_file * self.sq_size + self.sq_size // 2
        p2_y = self.board_y + y2_rank * self.sq_size + self.sq_size // 2

        dx = p2_x - p1_x
        dy = p2_y - p1_y
        dist = math.hypot(dx, dy)
        if dist < 5:
            return

        ux = dx / dist
        uy = dy / dist
        nx = -uy
        ny = ux

        head_len = 32
        head_w = 26
        # Pull back slightly from square center so piece underneath remains visible
        target_x = p2_x - ux * 14
        target_y = p2_y - uy * 14

        shaft_end_x = target_x - ux * head_len
        shaft_end_y = target_y - uy * head_len

        # Draw thick shaft
        draw.line([(p1_x, p1_y), (shaft_end_x, shaft_end_y)], fill=color[:3], width=width)

        # Draw triangular arrowhead
        tip = (target_x, target_y)
        left = (shaft_end_x + nx * (head_w / 2), shaft_end_y + ny * (head_w / 2))
        right = (shaft_end_x - nx * (head_w / 2), shaft_end_y - ny * (head_w / 2))
        draw.polygon([tip, left, right], fill=color[:3])

    def render_frame(self, board: chess.Board, last_move=None, move_history=None, 
                     white_clock="09:45", black_clock="09:50", active_player="White",
                     eval_score=0.0, subtitle_text="", strategy_name=""):
        if move_history is None:
            move_history = []

        img = Image.new("RGB", (self.width, self.height), (20, 23, 28))
        draw = ImageDraw.Draw(img)

        # ------------------------------------------------------------------
        # 1. TOP HEADER
        # ------------------------------------------------------------------
        draw.rectangle([0, 0, self.width, 50], fill=(14, 16, 20))
        draw.rectangle([0, 48, self.width, 50], fill=(218, 165, 32)) # Gold accent
        draw.text((40, 12), "CHESS GRANDMASTER BATTLE  |  RAPID BLITZ CHAMPIONSHIP", font=self.title_font, fill=(255, 255, 255))
        draw.text((1520, 14), "STOCKFISH 19 (3600+ ELO)", font=self.player_font, fill=(0, 230, 160))

        # ------------------------------------------------------------------
        # 2. LEFT SIDEBAR: PERFECT PROPORTIONS & CIRCULAR AVATARS
        # ------------------------------------------------------------------
        sidebar_x = 40
        sidebar_w = 810

        # --- PLAYER 2: BLACK CARD (Top) ---
        b_card_y = 65
        b_card_h = 90
        b_active = (active_player == "Black")
        b_border = (0, 230, 255) if b_active else (45, 52, 64)
        draw.rectangle([sidebar_x, b_card_y, sidebar_x + sidebar_w, b_card_y + b_card_h], fill=(28, 32, 40), outline=b_border, width=2)

        # Circular Avatar for Black Player
        av_cx, av_cy, av_r = sidebar_x + 50, b_card_y + 45, 34
        draw.ellipse([av_cx - av_r, av_cy - av_r, av_cx + av_r, av_cy + av_r], fill=(15, 18, 24), outline=(0, 230, 255) if b_active else (80, 90, 110), width=3)
        draw.text((av_cx - 18, av_cy - 22), "\u265A", font=self.avatar_font, fill=(240, 240, 240))

        # Player Details
        draw.text((sidebar_x + 105, b_card_y + 18), "GM Victor \"The Iron Defense\"", font=self.player_font, fill=(255, 255, 255))
        draw.text((sidebar_x + 105, b_card_y + 48), "Grandmaster  |  Rating: 2865  |  Pieces: Black", font=self.log_font, fill=(160, 175, 195))

        # Black Clock Box
        draw.rectangle([sidebar_x + sidebar_w - 150, b_card_y + 18, sidebar_x + sidebar_w - 20, b_card_y + 72], 
                       fill=(18, 21, 26), outline=(0, 230, 255) if b_active else (55, 62, 75), width=2)
        clock_col = (0, 240, 255) if b_active else (180, 185, 195)
        draw.text((sidebar_x + sidebar_w - 128, b_card_y + 28), black_clock, font=self.clock_font, fill=clock_col)

        # --- DYNAMIC STRATEGY / TACTIC BADGE ---
        strat_y = 165
        strat_h = 36
        draw.rectangle([sidebar_x, strat_y, sidebar_x + sidebar_w, strat_y + strat_h], fill=(22, 28, 38), outline=(218, 165, 32), width=1)
        strat_display = strategy_name if strategy_name else "THEORY: Sicilian Defense (Najdorf Variation)"
        draw.text((sidebar_x + 15, strat_y + 7), "STRATEGY:", font=self.log_bold, fill=(218, 165, 32))
        draw.text((sidebar_x + 125, strat_y + 8), strat_display, font=self.log_font, fill=(0, 230, 255))

        # --- MOVE LOG CONTAINER (Center) ---
        log_y = 210
        log_h = 550
        draw.rectangle([sidebar_x, log_y, sidebar_x + sidebar_w, log_y + log_h], fill=(18, 21, 26), outline=(45, 52, 64), width=2)

        # Log Header Bar
        draw.rectangle([sidebar_x, log_y, sidebar_x + sidebar_w, log_y + 44], fill=(26, 30, 38))
        draw.text((sidebar_x + 25, log_y + 12), "MOVE #", font=self.log_bold, fill=(170, 180, 195))
        draw.text((sidebar_x + 150, log_y + 12), "WHITE (GM Alexander)", font=self.log_bold, fill=(255, 215, 0))
        draw.text((sidebar_x + 450, log_y + 12), "BLACK (GM Victor)", font=self.log_bold, fill=(0, 230, 255))
        draw.text((sidebar_x + 720, log_y + 12), "EVAL", font=self.log_bold, fill=(170, 180, 195))

        # Display last 13 moves in log
        visible_moves = move_history[-13:]
        for idx, item in enumerate(visible_moves):
            row_y = log_y + 54 + idx * 39
            is_active_row = (idx == len(visible_moves) - 1)
            
            # Row background
            if is_active_row:
                draw.rectangle([sidebar_x + 3, row_y - 4, sidebar_x + sidebar_w - 3, row_y + 32], fill=(36, 44, 56), outline=(218, 165, 32), width=1)
            elif idx % 2 == 1:
                draw.rectangle([sidebar_x + 3, row_y - 4, sidebar_x + sidebar_w - 3, row_y + 32], fill=(22, 25, 32))

            draw.text((sidebar_x + 30, row_y + 4), f"{item.get('num', '')}.", font=self.log_bold, fill=(140, 150, 165))
            draw.text((sidebar_x + 150, row_y + 4), item.get('white', ''), font=self.log_font, fill=(255, 255, 255))
            draw.text((sidebar_x + 450, row_y + 4), item.get('black', ''), font=self.log_font, fill=(220, 220, 225))

            # Evaluation badge
            eval_txt = str(item.get('eval', '+0.0'))
            badge_bg = (30, 70, 45) if '+' in eval_txt else (70, 30, 30)
            draw.rectangle([sidebar_x + 715, row_y + 2, sidebar_x + 785, row_y + 26], fill=badge_bg)
            draw.text((sidebar_x + 728, row_y + 4), eval_txt, font=self.badge_font, fill=(255, 255, 255))

        # --- PLAYER 1: WHITE CARD (Bottom) ---
        w_card_y = 770
        w_card_h = 100
        w_active = (active_player == "White")
        w_border = (218, 165, 32) if w_active else (45, 52, 64)
        draw.rectangle([sidebar_x, w_card_y, sidebar_x + sidebar_w, w_card_y + w_card_h], fill=(28, 32, 40), outline=w_border, width=2)

        # Circular Avatar for White Player
        w_cx, w_cy, w_r = sidebar_x + 55, w_card_y + 50, 36
        draw.ellipse([w_cx - w_r, w_cy - w_r, w_cx + w_r, w_cy + w_r], fill=(235, 235, 240), outline=(218, 165, 32) if w_active else (180, 190, 205), width=3)
        draw.text((w_cx - 20, w_cy - 24), "\u2654", font=self.avatar_font, fill=(20, 20, 20)) # Dark king glyph inside bright circle for high contrast!

        # White Details
        draw.text((sidebar_x + 115, w_card_y + 22), "GM Alexander \"The Tactician\"", font=self.player_font, fill=(255, 255, 255))
        draw.text((sidebar_x + 115, w_card_y + 54), "Grandmaster  |  Rating: 2845  |  Pieces: White", font=self.log_font, fill=(160, 175, 195))

        # White Clock Box
        draw.rectangle([sidebar_x + sidebar_w - 150, w_card_y + 22, sidebar_x + sidebar_w - 20, w_card_y + 78], 
                       fill=(18, 21, 26), outline=(218, 165, 32) if w_active else (55, 62, 75), width=2)
        w_clock_col = (255, 215, 0) if w_active else (180, 185, 195)
        draw.text((sidebar_x + sidebar_w - 128, w_card_y + 34), white_clock, font=self.clock_font, fill=w_clock_col)

        # ------------------------------------------------------------------
        # 3. VERTICAL ADVANTAGE EVALUATION BAR (Between sidebar & board)
        # ------------------------------------------------------------------
        eval_bar_x = 880
        eval_bar_y = self.board_y
        eval_bar_w = 26
        eval_bar_h = self.board_size

        # Clamp eval score between -10 and +10 for visual bar
        try:
            val = float(str(eval_score).replace('#', '10').replace('M', '10'))
        except Exception:
            val = 0.0
        val = max(-10.0, min(10.0, val))

        # 50% is equal (+0.0). Positive means White advantage (white bar rises from bottom)
        white_ratio = 0.5 + (val / 20.0)
        split_h = int(eval_bar_h * (1.0 - white_ratio))

        # Black part (top)
        draw.rectangle([eval_bar_x, eval_bar_y, eval_bar_x + eval_bar_w, eval_bar_y + split_h], fill=(45, 50, 60))
        # White part (bottom)
        draw.rectangle([eval_bar_x, eval_bar_y + split_h, eval_bar_x + eval_bar_w, eval_bar_y + eval_bar_h], fill=(240, 240, 245))
        draw.rectangle([eval_bar_x, eval_bar_y, eval_bar_x + eval_bar_w, eval_bar_y + eval_bar_h], outline=(80, 90, 110), width=2)

        # ------------------------------------------------------------------
        # 4. RIGHT PANEL: TOURNAMENT CHESSBOARD
        # ------------------------------------------------------------------
        # Outer Board Frame
        draw.rectangle([self.board_x - 12, self.board_y - 12, self.board_x + self.board_size + 12, self.board_y + self.board_size + 12], 
                       fill=(32, 36, 44), outline=(65, 75, 90), width=3)

        highlight_sqs = []
        if last_move:
            highlight_sqs = [last_move.from_square, last_move.to_square]

        king_in_check_sq = None
        if board.is_check():
            king_in_check_sq = board.king(board.turn)

        # Draw 64 squares
        for rank in range(8):
            for file in range(8):
                sq = chess.square(file, 7 - rank)
                sq_x = self.board_x + file * self.sq_size
                sq_y = self.board_y + rank * self.sq_size

                is_light = (file + rank) % 2 == 0
                sq_color = (238, 238, 210) if is_light else (118, 150, 86)

                # Last move square highlights (Warm Golden Amber)
                if sq in highlight_sqs:
                    sq_color = (245, 246, 130) if is_light else (186, 202, 68)

                # King in check highlight (Crimson Glow)
                if sq == king_in_check_sq:
                    sq_color = (235, 60, 60)

                draw.rectangle([sq_x, sq_y, sq_x + self.sq_size, sq_y + self.sq_size], fill=sq_color)

                # Board Coordinates (Rank numbers 1-8 and File letters a-h)
                if file == 0:
                    c_col = (118, 150, 86) if is_light else (238, 238, 210)
                    draw.text((sq_x + 6, sq_y + 4), str(8 - rank), font=self.coord_font, fill=c_col)
                if rank == 7:
                    c_col = (118, 150, 86) if is_light else (238, 238, 210)
                    draw.text((sq_x + self.sq_size - 18, sq_y + self.sq_size - 22), chr(ord('a') + file), font=self.coord_font, fill=c_col)

                # Draw Chess Pieces
                piece = board.piece_at(sq)
                if piece:
                    symbol = PIECE_GLYPHS.get(piece.symbol(), '')
                    is_white_piece = piece.color == chess.WHITE
                    p_color = (255, 255, 255) if is_white_piece else (20, 20, 20)
                    
                    # High contrast shadow + main piece
                    draw.text((sq_x + 14, sq_y + 8), symbol, font=self.piece_font, fill=(0, 0, 0) if is_white_piece else (210, 210, 210))
                    draw.text((sq_x + 12, sq_y + 6), symbol, font=self.piece_font, fill=p_color)

        # ------------------------------------------------------------------
        # 5. TACTICAL MOVE ARROWS (From -> To in Bold Crimson/Red)
        # ------------------------------------------------------------------
        if last_move:
            self.draw_arrow(draw, last_move.from_square, last_move.to_square, color=(235, 55, 55), width=12)

        # ------------------------------------------------------------------
        # 6. BOTTOM SUBTITLE & COMMENTARY BANNER
        # ------------------------------------------------------------------
        sub_y = 920
        sub_h = 130
        draw.rectangle([40, sub_y, self.width - 40, sub_y + sub_h], fill=(16, 18, 22), outline=(50, 56, 68), width=2)
        
        badge_color = (218, 165, 32) if active_player == "White" else (0, 230, 255)
        draw.rectangle([60, sub_y + 15, 240, sub_y + 48], fill=badge_color)
        speaker_name = "GM ALEXANDER" if active_player == "White" else "GM VICTOR"
        draw.text((75, sub_y + 19), speaker_name, font=self.sub_bold, fill=(0, 0, 0))

        draw.text((60, sub_y + 62), f"\"{subtitle_text}\"", font=self.sub_font, fill=(255, 255, 255))

        return img
