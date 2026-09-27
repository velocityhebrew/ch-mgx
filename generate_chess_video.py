import asyncio
import os
import sys
import time
import subprocess
from datetime import timedelta
import chess

from board_renderer import ChessBoardRenderer
from match_narrator import ChessNarrator
from chess_gameplay import MATCH_MOVES
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

async def generate_all():
    print("=" * 70)
    print("      CHESS GRANDMASTER SHOWDOWN - DUAL CHARACTER MATCH GENERATOR")
    print("=" * 70)
    print(f"Total Moves to play: {len(MATCH_MOVES)}")
    print(f"White Character: GM Alexander (Voice: en-US-GuyNeural)")
    print(f"Black Character: GM Victor (Voice: en-US-ChristopherNeural)")
    print(f"Output Video: {OUTPUT_VIDEO}")
    print("=" * 70)

    renderer = ChessBoardRenderer()
    narrator = ChessNarrator(VOICE_DIR)

    board = chess.Board()
    move_history = []
    
    # 10-minute Rapid Clocks (600 seconds)
    white_seconds = 600.0
    black_seconds = 600.0

    segment_files = []
    subtitles = []
    total_elapsed = 0.0

    # Process each move
    for idx, move_data in enumerate(MATCH_MOVES, 1):
        player = move_data["player"]
        uci_move = move_data["move"]
        san_move = move_data["san"]
        eval_score = move_data["eval"]
        dialogue = move_data["dialogue"]

        print(f"\n[*] Processing Move {idx}/{len(MATCH_MOVES)}: [{player}] {san_move}")

        # 1. Generate Voiceover Dialogue Clip
        clip_id = f"move_{idx:03d}"
        audio_path = await narrator.generate_dialogue(clip_id, player, dialogue)
        audio_dur = narrator.get_audio_duration(audio_path)
        move_dur = audio_dur + 0.8  # Add short natural breathing pause

        # 2. Update Clocks
        if player == "White":
            white_seconds -= (audio_dur + 2.0)
        else:
            black_seconds -= (audio_dur + 2.0)

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

        # 5. Render Board Frame
        frame_img = renderer.render_frame(
            board=board,
            last_move=move_obj,
            move_history=move_history,
            white_clock=format_clock(white_seconds),
            black_clock=format_clock(black_seconds),
            active_player=player,
            eval_score=eval_score,
            subtitle_text=dialogue
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

        # 7. Encode Video Segment with FFmpeg
        seg_mp4 = os.path.join(RECORDINGS_DIR, f"seg_{idx:03d}.mp4").replace("\\", "/")
        segment_files.append(seg_mp4)

        if not (os.path.exists(seg_mp4) and os.path.getsize(seg_mp4) > 5000):
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", str(move_dur), "-i", frame_path,
                "-i", audio_path.replace("\\", "/"),
                "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-af", f"apad=whole_dur={move_dur}",
                "-shortest",
                seg_mp4
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  [+] Segment encoded: {seg_mp4} ({move_dur:.1f}s)")
        else:
            print(f"  [+] Segment cached: {seg_mp4} ({move_dur:.1f}s)")

    # 8. Write Subtitles File (.srt)
    print("\n[*] Writing subtitles file...")
    with open(SRT_FILE, "w", encoding="utf-8") as f:
        for i, sub in enumerate(subtitles, 1):
            f.write(f"{i}\n")
            f.write(f"{format_srt_time(sub['start'])} --> {format_srt_time(sub['end'])}\n")
            f.write(f"[{sub['speaker']}]: {sub['text']}\n\n")
    print(f"[+] Subtitles saved: {SRT_FILE}")

    # 9. Concat all segments into Final Match Video
    concat_list = os.path.join(RECORDINGS_DIR, "chess_concat_list.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for s in segment_files:
            f.write(f"file '{s}'\n")

    print("[*] Merging all segments into master Grandmaster Match Video with FFmpeg...")
    final_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        OUTPUT_VIDEO
    ]
    subprocess.run(final_cmd, check=True)

    # Clean up intermediate segment files
    for s in segment_files:
        try:
            os.remove(s)
        except Exception:
            pass
    try:
        os.remove(concat_list)
    except Exception:
        pass

    # 10. Generate YouTube Thumbnail
    thumb_path = generate_youtube_thumbnail()

    size_mb = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print("\n" + "=" * 70)
    print("[SUCCESS] GRANDMASTER CHESS MATCH VIDEO & THUMBNAIL READY!")
    print(f"Video File: {OUTPUT_VIDEO}")
    print(f"Video Size: {size_mb:.2f} MB")
    print(f"Duration:   {total_elapsed:.1f} seconds ({total_elapsed/60.0:.2f} minutes)")
    print(f"Subtitles:  {SRT_FILE}")
    print(f"Thumbnail:  {thumb_path}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(generate_all())
