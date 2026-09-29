import asyncio
import os
import sys
import time
import subprocess
from datetime import timedelta
import chess

from board_renderer import ChessBoardRenderer
from match_narrator import ChessNarrator
from grandmaster_database import get_game_of_the_day, parse_game_moves
from thumbnail_generator import generate_youtube_thumbnail

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
VOICE_DIR = os.path.join(BASE_DIR, "voiceover")
FRAMES_DIR = os.path.join(RECORDINGS_DIR, "frames")
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)

OUTPUT_VIDEO = os.path.join(RECORDINGS_DIR, "grandmaster_chess_battle.mp4")
SRT_FILE = os.path.join(RECORDINGS_DIR, "chess_subtitles.srt")

def format_clock(seconds_left: float) -> str:
    s = max(0, int(seconds_left))
    mins, secs = divmod(s, 60)
    return f"{mins:02d}:{secs:02d}"

def format_srt_time(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

async def generate_all(game_info=None):
    if not game_info:
        game_info = get_game_of_the_day()

    moves = parse_game_moves(game_info)
    white_player = game_info.get("white_name", "White")
    black_player = game_info.get("black_name", "Black")

    print("=" * 70)
    print("      CHESS GRANDMASTER SHOWDOWN - 1080P 60FPS BROADCAST SUITE")
    print("=" * 70)
    print(f"Match: {white_player} vs {black_player}")
    print(f"Tournament/Event: {game_info.get('event', 'Championship')}")
    print(f"Opening: {game_info.get('opening', 'Grandmaster Theory')}")
    print(f"Total Moves to play: {len(moves)} plies")
    print(f"Output Video: {OUTPUT_VIDEO}")
    print("=" * 70)

    renderer = ChessBoardRenderer()
    narrator = ChessNarrator(VOICE_DIR)

    board = chess.Board()
    move_history = []
    
    # 15-minute Rapid Clocks (900 seconds)
    white_seconds = 900.0
    black_seconds = 900.0

    segment_files = []
    subtitles = []
    total_elapsed = 0.0

    # Clear old segments for clean generation
    concat_list_file = os.path.join(RECORDINGS_DIR, "concat_list.txt")
    if os.path.exists(concat_list_file):
        try: os.remove(concat_list_file)
        except Exception: pass

    for idx, move_data in enumerate(moves, 1):
        player = move_data["player"]
        uci_move = move_data["move"]
        san_move = move_data["san"]
        eval_score = move_data["eval"]
        dialogue = move_data["dialogue"]
        strategy = move_data.get("strategy", "")

        # 1. Generate Voiceover Dialogue Clip
        clip_id = f"move_{idx:03d}"
        audio_path = await narrator.generate_dialogue(clip_id, player, dialogue)
        audio_dur = narrator.get_audio_duration(audio_path)
        move_dur = audio_dur + 0.6  # Short natural pause

        # 2. Update Clocks
        if player == "White":
            white_seconds -= (audio_dur + 1.5)
        else:
            black_seconds -= (audio_dur + 1.5)

        # 3. Make move on board
        move_obj = chess.Move.from_uci(uci_move)
        board.push(move_obj)

        # 4. Update Move History Table for Left Sidebar
        move_num = (idx + 1) // 2
        if player == "White":
            move_history.append({
                "num": move_num,
                "white": san_move,
                "black": "...",
                "eval": eval_score
            })
        else:
            if move_history:
                move_history[-1]["black"] = san_move
                move_history[-1]["eval"] = eval_score

        # 5. Render Board Frame with Dynamic Player Names and Strategy Badge
        frame_img = renderer.render_frame(
            board=board,
            last_move=move_obj,
            move_history=move_history,
            white_clock=format_clock(white_seconds),
            black_clock=format_clock(black_seconds),
            active_player=player,
            eval_score=eval_score,
            subtitle_text=dialogue,
            strategy_name=strategy,
            white_name=white_player,
            black_name=black_player,
            white_title=f"Grandmaster  |  Rating: {game_info.get('white_rating', '2800')}  |  Pieces: White",
            black_title=f"Grandmaster  |  Rating: {game_info.get('black_rating', '2800')}  |  Pieces: Black"
        )
        frame_path = os.path.join(FRAMES_DIR, f"frame_{idx:03d}.png").replace("\\", "/")
        frame_img.save(frame_path)

        # 6. Record Subtitle
        subtitles.append({
            "start": total_elapsed,
            "end": total_elapsed + move_dur,
            "speaker": player,
            "text": dialogue
        })
        total_elapsed += move_dur

        # 7. Encode Video Segment with FFmpeg (1080p 60FPS)
        seg_mp4 = os.path.join(RECORDINGS_DIR, f"seg_{idx:03d}.mp4").replace("\\", "/")
        segment_files.append(seg_mp4)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", str(move_dur), "-i", frame_path,
            "-i", audio_path.replace("\\", "/"),
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-r", "60",
            "-c:a", "aac", "-b:a", "192k",
            "-af", f"apad=whole_dur={move_dur}",
            "-shortest",
            seg_mp4
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if idx % 10 == 0 or idx == len(moves):
            print(f"[*] Processed move {idx}/{len(moves)} ({san_move}) - Board & Voice Ready")

    # 8. Generate Subtitle File (.srt)
    with open(SRT_FILE, "w", encoding="utf-8") as srt_out:
        for i, sub in enumerate(subtitles, 1):
            s_start = format_srt_time(sub["start"])
            s_end = format_srt_time(sub["end"])
            speaker_tag = f"[{white_player}]" if sub["speaker"] == "White" else f"[{black_player}]"
            srt_out.write(f"{i}\n{s_start} --> {s_end}\n{speaker_tag} {sub['text']}\n\n")
    print(f"[+] Subtitles generated at: {SRT_FILE}")

    # 9. Concat Segments into Single Video
    print("[*] Concatenating all segment files into final master video...")
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for seg in segment_files:
            f.write(f"file '{os.path.basename(seg)}'\n")

    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        OUTPUT_VIDEO
    ]
    subprocess.run(concat_cmd, cwd=RECORDINGS_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[SUCCESS] Final 1080p 60FPS Video Exported to: {OUTPUT_VIDEO}")
    return OUTPUT_VIDEO

if __name__ == "__main__":
    asyncio.run(generate_all())
