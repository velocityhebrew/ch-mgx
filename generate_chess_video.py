import asyncio
import json
import os
import subprocess
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
CHAPTERS_FILE = os.path.join(RECORDINGS_DIR, "chapters.json")

FPS = 60
ANIM_DUR = 0.5
ANIM_FRAMES = int(ANIM_DUR * FPS)

# Natural broadcast pacing: let every narrated move breathe. The full game is
# always played out; nothing is compressed to hit a fixed runtime.
MOVE_PAUSE = 1.4
CLIMAX_BONUS = 1.6
CHECKMATE_BONUS = 1.4
MIN_TARGET_SECONDS = 420.0  # the game source filters for 78+ plies; warn if we land short


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


def spoken_eval(ev) -> str:
    s = str(ev).strip()
    if s.startswith("#"):
        return "a forced checkmate"
    try:
        v = float(s.replace("+", ""))
    except ValueError:
        return s
    if abs(v) < 0.05:
        return "dead level"
    return f"plus {v:.1f}" if v > 0 else f"minus {abs(v):.1f}"


def probe_duration(path: str):
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            text=True,
        )
        return float(out.strip())
    except Exception:
        return None


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


def add_chapter(chapters, at, title, force=False, min_gap=10.0):
    """Keep YouTube-valid chapters (first at 0:00, at least 10s apart)."""
    at = max(0.0, float(at))
    title = (title or "").strip("! ").strip()
    if not title:
        title = "Highlights"
    if chapters and at - chapters[-1]["time"] < min_gap:
        if force:
            chapters[-1] = {"time": at, "title": title}
        return
    chapters.append({"time": at, "title": title})


def finalize_chapters(chapters):
    """Sort chronologically and drop chapters that are less than 10s apart."""
    ordered = sorted(chapters, key=lambda ch: ch["time"])
    cleaned = []
    for ch in ordered:
        if not cleaned or ch["time"] - cleaned[-1]["time"] >= 10.0:
            cleaned.append(ch)
    if not cleaned or cleaned[0]["time"] > 0:
        cleaned.insert(0, {"time": 0.0, "title": "Intro"})
    return cleaned


async def generate_all(game_info=None, max_moves=None):
    if not game_info:
        game_info = get_game_of_the_day()

    moves = parse_game_moves(game_info)
    if max_moves:
        moves = moves[:max_moves]
    white_player = game_info.get("white_name", "White")
    black_player = game_info.get("black_name", "Black")
    white_clean = white_player.replace("GM ", "")
    black_clean = black_player.replace("GM ", "")
    total_full_moves = (len(moves) + 1) // 2
    climax_ply = int(game_info.get("climax_ply") or 0)

    print("=" * 70)
    print("      CHESS MAGIX - 1080P 60FPS BROADCAST SUITE")
    print("=" * 70)
    print(f"Match: {white_player} vs {black_player}")
    print(f"Event: {game_info.get('event', 'Championship')}")
    print(f"Opening: {game_info.get('opening', 'Grandmaster Theory')}")
    print(f"Moves: {len(moves)} plies | full game, natural pacing")
    print("=" * 70)

    renderer = ChessBoardRenderer()
    narrator = ChessNarrator(VOICE_DIR)

    board = chess.Board()
    move_history = []
    white_seconds = 900.0
    black_seconds = 900.0

    segment_files = []
    subtitles = []
    chapters = [{"time": 0.0, "title": "Intro"}]
    total_elapsed = 0.0
    climax_snapshot = None
    last_move_obj = None
    last_san_display = ""

    def add_subtitle(start, end, speaker, text):
        subtitles.append({"start": start, "end": end, "speaker": speaker, "text": text})

    # ------------------------------------------------------------------
    # INTRO CARD (with the day's hook so viewers know why to stay)
    # ------------------------------------------------------------------
    hook = str(game_info.get("climax_hook", "")).strip()
    intro_text = (
        f"Welcome back to Chess Magix! {white_clean} versus {black_clean}, "
        f"at {game_info.get('event', 'the championship')}. "
    )
    if hook:
        intro_text += f"Today: {hook} "
    intro_text += "Let's get into it!"
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
    # PRE-GAME STORY (sets the stakes before the first move)
    # ------------------------------------------------------------------
    story_text = str(game_info.get("story_summary") or "").strip()
    if not story_text:
        story_text = (
            f"The stage is set at {game_info.get('event', 'the championship')}. "
            f"{white_clean} versus {black_clean}. "
            f"{game_info.get('theme', 'A battle of styles')}."
        )
    if len(story_text) > 500:
        story_text = story_text[:500].rsplit(" ", 1)[0].rstrip(".,;:") + "."
    story_audio = await narrator.generate_dialogue("story", "Host", story_text)
    story_dur = narrator.get_audio_duration(story_audio) + 0.8
    story_start = total_elapsed
    story_img = renderer.render_frame(
        chess.Board(), last_move=None, move_history=[],
        white_clock="15:00", black_clock="15:00", active_player="Host",
        eval_score=0.0, subtitle_text=story_text,
        strategy_name=f"Opening: {game_info.get('opening', 'Grandmaster Theory')}",
        white_name=white_player, black_name=black_player,
        white_title=f"Grandmaster  •  {game_info.get('white_rating', '2800')}",
        black_title=f"Grandmaster  •  {game_info.get('black_rating', '2800')}",
        move_label="THE STAGE IS SET",
        event_name=game_info.get("event", "Grandmaster Classic"),
        progress=0.0, subtitle_speaker_name="Chess Magix",
        show_replay_badge=False,
    )
    story_frame = os.path.join(FRAMES_DIR, "story.png")
    story_img.save(story_frame)
    seg = os.path.join(RECORDINGS_DIR, "seg_001_story.mp4")
    encode_still_segment(story_frame, story_audio, story_dur, seg)
    segment_files.append(seg)
    add_subtitle(story_start, story_start + story_dur, "Host", story_text)
    add_chapter(chapters, story_start, "The Story")
    total_elapsed += story_dur
    add_chapter(chapters, total_elapsed, "The Battle Begins")
    print("[*] Pre-game story ready")

    # ------------------------------------------------------------------
    # MOVES (every ply of the game, no compression)
    # ------------------------------------------------------------------
    halfway_ply = len(moves) // 2 if len(moves) >= 40 else 0
    for idx, move_data in enumerate(moves, 1):
        player = move_data["player"]
        uci_move = move_data["move"]
        san_move = move_data["san"]
        eval_score = move_data["eval"]
        dialogue = move_data["dialogue"]
        strategy = move_data.get("strategy", "")
        note = move_data.get("note", "")
        san_display = san_move + note

        clip_id = f"move_{idx:03d}"
        audio_path = await narrator.generate_dialogue(clip_id, player, dialogue)
        audio_dur = narrator.get_audio_duration(audio_path)

        move_dur = audio_dur + MOVE_PAUSE
        if climax_ply and idx == climax_ply:
            move_dur += CLIMAX_BONUS
        if "#" in san_move:
            move_dur += CHECKMATE_BONUS
        move_dur = max(move_dur, ANIM_DUR + 0.4)
        move_start = total_elapsed

        if player == "White":
            white_seconds -= (audio_dur + 1.5)
        else:
            black_seconds -= (audio_dur + 1.5)

        move_obj = chess.Move.from_uci(uci_move)
        board.push(move_obj)

        move_num = (idx + 1) // 2
        if player == "White":
            move_history.append({"num": move_num, "white": san_display, "black": "...", "eval": eval_score})
        else:
            if move_history:
                move_history[-1]["black"] = san_display
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
            progress=idx / max(1, len(moves)),
            last_move_san=san_display,
        )

        # Base frame with the moving piece hidden, then slide it in over ANIM_FRAMES.
        # The notation pill only appears once the move has landed.
        anim_kwargs = dict(render_kwargs, last_move_san="")
        base = renderer.render_frame(board, last_move=move_obj, hide_piece_sq=move_obj.to_square,
                                     show_arrow=False, **anim_kwargs)
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

        if climax_ply and idx == climax_ply:
            climax_snapshot = {
                "board": board.copy(),
                "last_move": move_obj,
                "history": [dict(h) for h in move_history],
                "san": san_move,
                "san_display": san_display,
                "player_name": white_player if player == "White" else black_player,
                "eval": eval_score,
                "strategy": strategy,
                "move_num": move_num,
                "white_clock": format_clock(white_seconds),
                "black_clock": format_clock(black_seconds),
                "progress": idx / max(1, len(moves)),
                "time": move_start,
            }

        seg = os.path.join(RECORDINGS_DIR, f"seg_{idx:03d}.mp4")
        anim_pattern = os.path.join(FRAMES_DIR, f"anim_{idx:03d}_%02d.png")
        encode_move_segment(anim_pattern, os.path.join(RECORDINGS_DIR, final_rel),
                            audio_path, move_dur, seg)
        segment_files.append(seg)
        add_subtitle(move_start, move_start + move_dur, player, dialogue)
        total_elapsed += move_dur
        last_move_obj = move_obj
        last_san_display = san_display

        if halfway_ply and idx == halfway_ply:
            half_strategy = str(strategy).lstrip("! ").strip().lower() or "keeping the pressure on"
            half_text = (
                f"Halfway check-in. We are at move {move_num}. "
                f"The evaluation is {spoken_eval(eval_score)}, and the key idea right now is "
                f"{half_strategy}. The tension is building."
            )
            half_audio = await narrator.generate_dialogue("halfway_review", "Host", half_text)
            half_dur = narrator.get_audio_duration(half_audio) + 0.8
            half_img = renderer.render_frame(
                board, last_move=move_obj, move_history=move_history,
                white_clock=format_clock(white_seconds), black_clock=format_clock(black_seconds),
                active_player="Host", eval_score=eval_score, subtitle_text=half_text,
                strategy_name=strategy, white_name=white_player, black_name=black_player,
                white_title=f"Grandmaster  •  {game_info.get('white_rating', '2800')}",
                black_title=f"Grandmaster  •  {game_info.get('black_rating', '2800')}",
                move_label=f"MOVE {move_num} / {total_full_moves}",
                event_name=game_info.get("event", "Grandmaster Classic"),
                progress=idx / max(1, len(moves)), last_move_san=san_move,
                subtitle_speaker_name="Chess Magix",
            )
            half_frame = os.path.join(FRAMES_DIR, "halfway_review.png")
            half_img.save(half_frame)
            seg = os.path.join(RECORDINGS_DIR, "seg_899_halfway_review.mp4")
            encode_still_segment(half_frame, half_audio, half_dur, seg)
            segment_files.append(seg)
            half_start = total_elapsed
            add_subtitle(half_start, half_start + half_dur, "Host", half_text)
            add_chapter(chapters, half_start, "Halfway Check-In")
            total_elapsed += half_dur
            print("[*] Halfway check-in ready")

        if idx % 20 == 1 and idx > 1:
            add_chapter(chapters, move_start, f"Move {move_num}: {strategy}")

        if idx % 10 == 0 or idx == len(moves):
            print(f"[*] Move {idx}/{len(moves)} ({san_move}) animated + voiced")

    # ------------------------------------------------------------------
    # RESULT
    # ------------------------------------------------------------------
    pgn = game_info.get("pgn", "")
    if "1-0" in pgn:
        result, summary = "1-0", "WHITE WINS"
        result_line = f"{white_clean} takes the game!"
    elif "0-1" in pgn:
        result, summary = "0-1", "BLACK WINS"
        result_line = f"{black_clean} takes the game!"
    else:
        result, summary = "1/2-1/2", "DRAW"
        result_line = "An honorable draw."

    # ------------------------------------------------------------------
    # TURNING-POINT ANALYSIS (re-live the signature move)
    # ------------------------------------------------------------------
    if climax_snapshot:
        cs = climax_snapshot
        strat = str(cs["strategy"]).lstrip("! ").strip() or "a brilliant tactical idea"
        strat_spoken = strat.lower() if strat.isupper() else strat
        recap_text = (
            f"The turning point came on move {cs['move_num']}: "
            f"{cs['player_name'].replace('GM ', '')} played {cs['san']}. "
            f"{strat_spoken}. The evaluation jumped to {spoken_eval(cs['eval'])}."
        )
        recap_audio = await narrator.generate_dialogue("climax_review", "Host", recap_text)
        recap_dur = narrator.get_audio_duration(recap_audio) + 0.8
        recap_img = renderer.render_frame(
            cs["board"], last_move=cs["last_move"], move_history=cs["history"],
            white_clock=cs["white_clock"], black_clock=cs["black_clock"], active_player="Host",
            eval_score=cs["eval"], subtitle_text=recap_text, strategy_name=cs["strategy"],
            white_name=white_player, black_name=black_player,
            white_title=f"Grandmaster  •  {game_info.get('white_rating', '2800')}",
            black_title=f"Grandmaster  •  {game_info.get('black_rating', '2800')}",
            move_label=f"MOVE {cs['move_num']} / {total_full_moves}",
            event_name=game_info.get("event", "Grandmaster Classic"),
            progress=cs["progress"], last_move_san=cs["san_display"],
            subtitle_speaker_name="Chess Magix",
        )
        recap_frame = os.path.join(FRAMES_DIR, "climax_review.png")
        recap_img.save(recap_frame)
        seg = os.path.join(RECORDINGS_DIR, "seg_900_climax_review.mp4")
        encode_still_segment(recap_frame, recap_audio, recap_dur, seg)
        segment_files.append(seg)
        recap_start = total_elapsed
        add_subtitle(recap_start, recap_start + recap_dur, "Host", recap_text)
        add_chapter(chapters, recap_start, f"Turning Point: {strat}", force=True)
        total_elapsed += recap_dur
        print("[*] Turning-point analysis ready")

    # ------------------------------------------------------------------
    # FINAL POSITION (hold on the board, then roll the outro card)
    # ------------------------------------------------------------------
    final_text = (
        f"The final position. {result_line} "
        f"{white_clean} and {black_clean} gave us a classic. "
        f"If you enjoyed the battle, subscribe for a new grandmaster masterpiece every day."
    )
    final_audio = await narrator.generate_dialogue("final_review", "Host", final_text)
    final_dur = narrator.get_audio_duration(final_audio) + 0.8
    final_img = renderer.render_frame(
        board, last_move=last_move_obj, move_history=move_history,
        white_clock=format_clock(white_seconds), black_clock=format_clock(black_seconds),
        active_player="Host", eval_score=moves[-1]["eval"] if moves else 0.0,
        subtitle_text=final_text, strategy_name="Final Position",
        white_name=white_player, black_name=black_player,
        white_title=f"Grandmaster  •  {game_info.get('white_rating', '2800')}",
        black_title=f"Grandmaster  •  {game_info.get('black_rating', '2800')}",
        move_label=f"FINAL  •  {total_full_moves} MOVES",
        event_name=game_info.get("event", "Grandmaster Classic"),
        progress=1.0, last_move_san=last_san_display,
        subtitle_speaker_name="Chess Magix",
    )
    final_frame = os.path.join(FRAMES_DIR, "final_position.png")
    final_img.save(final_frame)
    seg = os.path.join(RECORDINGS_DIR, "seg_998_final.mp4")
    final_start = total_elapsed
    encode_still_segment(final_frame, final_audio, final_dur, seg)
    segment_files.append(seg)
    add_subtitle(final_start, final_start + final_dur, "Host", final_text)
    add_chapter(chapters, final_start, "Final Position")
    total_elapsed += final_dur
    print("[*] Final position ready")

    # ------------------------------------------------------------------
    # OUTRO CARD
    # ------------------------------------------------------------------
    outro_text = (
        "And that's the game! Thanks for watching Chess Magix. "
        "See you tomorrow for another immortal classic!"
    )
    outro_audio = await narrator.generate_dialogue("outro", "Host", outro_text)
    outro_dur = narrator.get_audio_duration(outro_audio) + 0.8
    outro_img = renderer.render_outro(game_info, result_text=result, summary=summary)
    outro_frame = os.path.join(FRAMES_DIR, "outro.png")
    outro_img.save(outro_frame)
    seg = os.path.join(RECORDINGS_DIR, "seg_999_outro.mp4")
    outro_start = total_elapsed
    encode_still_segment(outro_frame, outro_audio, outro_dur, seg)
    segment_files.append(seg)
    add_subtitle(outro_start, outro_start + outro_dur, "Host", outro_text)
    # Keep the final chapter valid: YouTube requires every chapter to be >=10s.
    if outro_dur >= 10.0:
        add_chapter(chapters, outro_start, "Result & Subscribe")
    total_elapsed += outro_dur
    print("[*] Outro card ready")

    # ------------------------------------------------------------------
    # SUBTITLES + CHAPTERS + FINAL CONCAT
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

    chapters = finalize_chapters(chapters)
    with open(CHAPTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(chapters, f, indent=2)

    missing = [s for s in segment_files if not os.path.exists(s) or os.path.getsize(s) < 5000]
    if missing:
        raise RuntimeError("Missing or empty video segments: " + ", ".join(os.path.basename(s) for s in missing))

    concat_list_file = os.path.join(RECORDINGS_DIR, "concat_list.txt")
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for s in segment_files:
            f.write(f"file '{os.path.basename(s)}'\n")
    concat_cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_file,
                  "-c", "copy", "-movflags", "+faststart", OUTPUT_VIDEO]
    res = subprocess.run(concat_cmd, cwd=RECORDINGS_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg concat failed: {res.stderr.decode()[-800:]}")

    actual_duration = probe_duration(OUTPUT_VIDEO)
    if actual_duration is None:
        raise RuntimeError("Could not read the final video duration")
    if actual_duration < total_elapsed - 3.0:
        raise RuntimeError(
            f"Final video is shorter than rendered segments: {actual_duration:.1f}s vs {total_elapsed:.1f}s"
        )
    if actual_duration < MIN_TARGET_SECONDS:
        print(
            f"[WARNING] Final video is {actual_duration / 60:.1f} min, below the "
            f"{MIN_TARGET_SECONDS / 60:.0f}-minute target. Game has {len(moves)} plies."
        )

    print(f"[SUCCESS] Final 1080p 60FPS video ({actual_duration:.1f}s): {OUTPUT_VIDEO}")
    return {
        "video_path": OUTPUT_VIDEO,
        "duration": actual_duration,
        "chapters": chapters,
        "subtitles": SRT_FILE,
    }


if __name__ == "__main__":
    result = asyncio.run(generate_all())
    print(result["video_path"])
