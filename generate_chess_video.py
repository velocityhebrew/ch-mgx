import asyncio
import os
import subprocess
from datetime import timedelta
import chess

from board_renderer import ChessBoardRenderer
from match_narrator import ChessNarrator
from grandmaster_database import get_game_of_the_day, parse_game_moves

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
VOICE_DIR = os.path.join(BASE_DIR, "voiceover")
FRAMES_DIR = os.path.join(RECORDINGS_DIR, "frames")
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)

OUTPUT_VIDEO = os.path.join(RECORDINGS_DIR, "grandmaster_chess_battle.mp4")
SRT_FILE = os.path.join(RECORDINGS_DIR, "chess_subtitles.srt")

FPS = 60
ANIM_DUR = 0.35
ANIM_FRAMES = int(ANIM_DUR * FPS)
TARGET_SECONDS = 180.0
OUTRO_EST_SECONDS = 12.0


def format_clock(seconds_left: float) -> str:
    s = max(0, int(seconds_left))
    mins, secs = divmod(s, 60)
    return f"{mins:02d}:{secs:02d}"


def format_srt_time(seconds: float) -> str:
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - total_seconds) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def encode_still_segment(image_path, audio_path, duration, out_path):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(duration), "-i", image_path.replace("\\", "/"),
        "-i", audio_path.replace("\\", "/"),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-r", str(FPS), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-af", f"apad=whole_dur={duration}",
        "-t", str(duration),
        out_path,
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg still encode failed: {res.stderr.decode()[-800:]}")


def encode_move_segment(anim_pattern, still_path, audio_path, duration, out_path):
    hold = max(0.1, duration - ANIM_DUR)
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS), "-start_number", "0", "-i", anim_pattern.replace("\\", "/"),
        "-loop", "1", "-t", str(hold), "-i", still_path.replace("\\", "/"),
        "-i", audio_path.replace("\\", "/"),
        "-filter_complex",
        "[0:v]fps=60,format=yuv420p[a];[1:v]fps=60,format=yuv420p[b];[a][b]concat=n=2:v=1:a=0[v]",
        "-map", "[v]", "-map", "2:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k",
        "-af", f"apad=whole_dur={duration}",
        "-t", str(duration),
        out_path,
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg move encode failed: {res.stderr.decode()[-800:]}")


async def generate_all(game_info=None, max_moves=None):
    if not game_info:
        game_info = get_game_of_the_day()

    moves = parse_game_moves(game_info)
    if max_moves:
        moves = moves[:max_moves]
    white_player = game_info.get("white_name", "White")
    black_player = game_info.get("black_name", "Black")
    total_full_moves = (len(moves) + 1) // 2

    print("=" * 70)
    print("      CHESS MAGIX - 1080P 60FPS BROADCAST SUITE")
    print("=" * 70)
    print(f"Match: {white_player} vs {black_player}")
    print(f"Event: {game_info.get('event', 'Championship')}")
    print(f"Opening: {game_info.get('opening', 'Grandmaster Theory')}")
    print(f"Moves: {len(moves)} plies | animated slides + intro/outro")
    print("=" * 70)

    renderer = ChessBoardRenderer()
    narrator = ChessNarrator(VOICE_DIR)

    board = chess.Board()
    move_history = []
    white_seconds = 900.0
    black_seconds = 900.0

    segment_files = []
    subtitles = []
    total_elapsed = 0.0

    def add_subtitle(start, end, speaker, text):
        subtitles.append({"start": start, "end": end, "speaker": speaker, "text": text})

    # ------------------------------------------------------------------
    # INTRO CARD
    # ------------------------------------------------------------------
    intro_text = (
        f"Welcome back to Chess Magix! {white_player.replace('GM ', '')} versus "
        f"{black_player.replace('GM ', '')}, at {game_info.get('event', 'the championship')}. Let's go!"
    )
    intro_audio = await narrator.generate_dialogue("intro", "Host", intro_text)
    intro_dur = narrator.get_audio_duration(intro_audio) + 0.8
    intro_img = renderer.render_intro(game_info)
    intro_frame = os.path.join(FRAMES_DIR, "intro.png")
    intro_img.save(intro_frame)
    seg = os.path.join(RECORDINGS_DIR, "seg_000_intro.mp4")
    encode_still_segment(intro_frame, intro_audio, intro_dur, seg)
    segment_files.append(seg)
    add_subtitle(0, intro_dur, "Host", intro_text)
    total_elapsed += intro_dur
    print("[*] Intro card ready")

    # ------------------------------------------------------------------
    # MOVES
    # ------------------------------------------------------------------
    for idx, move_data in enumerate(moves, 1):
        player = move_data["player"]
        uci_move = move_data["move"]
        san_move = move_data["san"]
        eval_score = move_data["eval"]
        dialogue = move_data["dialogue"]
        strategy = move_data.get("strategy", "")

        clip_id = f"move_{idx:03d}"
        audio_path = await narrator.generate_dialogue(clip_id, player, dialogue)
        audio_dur = narrator.get_audio_duration(audio_path)
        # Pace short games toward ~3 min without adding more than 3s of pause per move
        remaining = len(moves) - idx + 1
        desired = (TARGET_SECONDS - total_elapsed - OUTRO_EST_SECONDS) / remaining
        move_dur = max(audio_dur + 0.55, min(desired, audio_dur + 3.0), ANIM_DUR + 0.4)

        if player == "White":
            white_seconds -= (audio_dur + 1.5)
        else:
            black_seconds -= (audio_dur + 1.5)

        move_obj = chess.Move.from_uci(uci_move)
        board.push(move_obj)

        move_num = (idx + 1) // 2
        if player == "White":
            move_history.append({"num": move_num, "white": san_move, "black": "...", "eval": eval_score})
        else:
            if move_history:
                move_history[-1]["black"] = san_move
                move_history[-1]["eval"] = eval_score

        render_kwargs = dict(
            move_history=move_history,
            white_clock=format_clock(white_seconds),
            black_clock=format_clock(black_seconds),
            active_player=player,
            eval_score=eval_score,
            subtitle_text=dialogue,
            strategy_name=strategy,
            white_name=white_player,
            black_name=black_player,
            white_title=f"Grandmaster  •  {game_info.get('white_rating', '2800')}",
            black_title=f"Grandmaster  •  {game_info.get('black_rating', '2800')}",
            move_label=f"MOVE {move_num} / {total_full_moves}",
            event_name=game_info.get("event", "Grandmaster Classic"),
        )

        # Base frame with the moving piece hidden, then slide it in over ANIM_FRAMES
        base = renderer.render_frame(board, last_move=move_obj, hide_piece_sq=move_obj.to_square,
                                     show_arrow=False, **render_kwargs)
        piece_sym = ('w' if player == "White" else 'b') + board.piece_at(move_obj.to_square).symbol().upper()
        x1, y1 = renderer.square_center(move_obj.from_square)
        x2, y2 = renderer.square_center(move_obj.to_square)

        for k in range(ANIM_FRAMES):
            t = (k + 1) / ANIM_FRAMES
            ease = 1 - (1 - t) ** 3
            cx, cy = x1 + (x2 - x1) * ease, y1 + (y2 - y1) * ease
            frame = base.copy()
            renderer.paste_piece(frame, piece_sym, cx, cy, size=98)
            frame.save(os.path.join(FRAMES_DIR, f"anim_{idx:03d}_{k:02d}.png"))
        final_rel = f"frames/frame_{idx:03d}.png"
        final_img = renderer.render_frame(board, last_move=move_obj, **render_kwargs)
        final_img.save(os.path.join(RECORDINGS_DIR, final_rel))

        seg = os.path.join(RECORDINGS_DIR, f"seg_{idx:03d}.mp4")
        anim_pattern = os.path.join(FRAMES_DIR, f"anim_{idx:03d}_%02d.png")
        encode_move_segment(anim_pattern, os.path.join(RECORDINGS_DIR, final_rel),
                            audio_path, move_dur, seg)
        segment_files.append(seg)
        add_subtitle(total_elapsed, total_elapsed + move_dur, player, dialogue)
        total_elapsed += move_dur

        if idx % 10 == 0 or idx == len(moves):
            print(f"[*] Move {idx}/{len(moves)} ({san_move}) animated + voiced")

    # ------------------------------------------------------------------
    # OUTRO CARD
    # ------------------------------------------------------------------
    pgn = game_info.get("pgn", "")
    if "1-0" in pgn:
        result, summary = "1-0", "WHITE WINS"
        result_line = f"{white_player.replace('GM ', '')} takes the game!"
    elif "0-1" in pgn:
        result, summary = "0-1", "BLACK WINS"
        result_line = f"{black_player.replace('GM ', '')} takes the game!"
    else:
        result, summary = "1/2-1/2", "DRAW"
        result_line = "An honorable draw."
    outro_text = (
        f"And that's the game! {result_line} What a battle. "
        f"If you loved this, subscribe to Chess Magix for daily grandmaster chess. See you tomorrow!"
    )
    outro_audio = await narrator.generate_dialogue("outro", "Host", outro_text)
    outro_dur = narrator.get_audio_duration(outro_audio) + 0.8
    outro_img = renderer.render_outro(game_info, result_text=result, summary=summary)
    outro_frame = os.path.join(FRAMES_DIR, "outro.png")
    outro_img.save(outro_frame)
    seg = os.path.join(RECORDINGS_DIR, "seg_999_outro.mp4")
    encode_still_segment(outro_frame, outro_audio, outro_dur, seg)
    segment_files.append(seg)
    add_subtitle(total_elapsed, total_elapsed + outro_dur, "Host", outro_text)
    total_elapsed += outro_dur
    print("[*] Outro card ready")

    # ------------------------------------------------------------------
    # SUBTITLES + FINAL CONCAT
    # ------------------------------------------------------------------
    with open(SRT_FILE, "w", encoding="utf-8") as srt_out:
        for i, sub in enumerate(subtitles, 1):
            if sub["speaker"] == "White":
                tag = f"[{white_player}]"
            elif sub["speaker"] == "Black":
                tag = f"[{black_player}]"
            else:
                tag = "[Chess Magix]"
            srt_out.write(f"{i}\n{format_srt_time(sub['start'])} --> {format_srt_time(sub['end'])}\n{tag} {sub['text']}\n\n")

    concat_list_file = os.path.join(RECORDINGS_DIR, "concat_list.txt")
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for s in segment_files:
            f.write(f"file '{os.path.basename(s)}'\n")
    concat_cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_file,
                  "-c", "copy", OUTPUT_VIDEO]
    subprocess.run(concat_cmd, cwd=RECORDINGS_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[SUCCESS] Final 1080p 60FPS video ({total_elapsed:.1f}s): {OUTPUT_VIDEO}")
    return OUTPUT_VIDEO


if __name__ == "__main__":
    asyncio.run(generate_all())