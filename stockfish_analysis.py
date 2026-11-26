"""
Real Stockfish analysis for the daily game.

Produces:
  - eval string after every ply
  - eval loss for the player who moved
  - move annotations (??, ?, !, !!)
  - the real turning point + badge/hook

Falls back silently when Stockfish is unavailable (local Windows dev), so the
existing simulated evaluation path still works.
"""

import os
import io
import shutil

import chess
import chess.engine
import chess.pgn

COMMON_PATHS = [
    "/usr/games/stockfish",
    "/usr/bin/stockfish",
    "/usr/local/bin/stockfish",
    r"C:\Program Files\Stockfish\stockfish.exe",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine", "stockfish", "stockfish.exe"),
]

PIECE_VALUES = {
    chess.PAWN: 5,
    chess.KNIGHT: 20,
    chess.BISHOP: 20,
    chess.ROOK: 30,
    chess.QUEEN: 50,
}


def find_stockfish():
    path = shutil.which("stockfish")
    if path:
        return path
    for candidate in COMMON_PATHS:
        if os.path.exists(candidate):
            return candidate
    return None


def _eval_from_score(score):
    """score is a PovScore from White's point of view."""
    if score.is_mate():
        mate = score.mate()
        return mate * 10000, f"#{mate}"
    cp = score.score()
    return cp, f"{cp / 100:+.1f}"


def _badge_for_move(san, captured, loss):
    if "#" in san:
        return "!! CHECKMATE", "THE FINAL BLOW?!"
    if captured is not None and captured.piece_type == chess.QUEEN:
        return "!! QUEEN CAPTURE", "THE QUEEN CAPTURE THAT DECIDED IT?!"
    if loss >= 2.0:
        return "!! THE BLUNDER", "THE MOVE THAT COST THE GAME?!"
    if loss <= -2.0:
        return "!! THE BRILLIANT MOVE", "THE MOVE THAT WON THE GAME?!"
    if "+" in san:
        return "!! TACTICAL CHECK", "THE CHECK THAT TURNED THE GAME?!"
    if "x" in san:
        return "!! TACTICAL CAPTURE", "CAN YOU SEE WHY THIS CAPTURE WINS?!"
    return "!! TURNING POINT", "THE MOVE THAT CHANGED EVERYTHING?!"


def analyse_game(game_info, depth=12):
    """Return analysis dict, or None if Stockfish is unavailable/fails."""
    path = find_stockfish()
    if not path:
        print("[stockfish] Binary not found; keeping simulated evaluations.")
        return None

    pgn = game_info.get("pgn", "")
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None or not game.mainline_moves():
        print("[stockfish] No moves to analyse.")
        return None

    moves = list(game.mainline_moves())
    sans = []
    board = chess.Board()
    for move in moves:
        try:
            sans.append(board.san(move))
            board.push(move)
        except Exception:
            print("[stockfish] Illegal PGN move; skipping analysis.")
            return None

    # Replay positions (start + after each ply).
    positions = [chess.Board()]
    replay = chess.Board()
    for move in moves:
        replay.push(move)
        positions.append(replay.copy())

    cps = []
    evals = []
    engine = None
    try:
        print(f"[stockfish] Analysing {len(positions)} positions at depth {depth}...")
        engine = chess.engine.SimpleEngine.popen_uci(path)
        try:
            # One thread keeps fixed-depth analysis deterministic.
            engine.configure({"Threads": 1, "Hash": 128})
        except Exception:
            pass
        engine_name = engine.id.get("name", "Stockfish")

        for idx, pos in enumerate(positions):
            if pos.is_checkmate():
                cp = -10000 if pos.turn == chess.WHITE else 10000
                ev = "#-1" if pos.turn == chess.WHITE else "#1"
            elif pos.is_game_over():
                cp, ev = 0, "0.0"
            else:
                info = engine.analyse(pos, chess.engine.Limit(depth=depth))
                cp, ev = _eval_from_score(info["score"].white())
            cps.append(cp)
            evals.append(ev)
    except Exception as e:
        print(f"[stockfish] Analysis failed: {e}")
        return None
    finally:
        if engine is not None:
            try:
                engine.quit()
            except Exception:
                pass

    losses = []
    annotations = []
    for i, san in enumerate(sans, 1):
        before = cps[i - 1]
        after = cps[i]
        mover_white = (i % 2 == 1)
        before_mover = before if mover_white else -before
        after_mover = after if mover_white else -after
        # If both positions are already a forced mate for the same side,
        # keeping the mate (even with a shorter/longer distance) is not a blunder.
        if abs(before) >= 9000 and abs(after) >= 9000 and (before > 0) == (after > 0):
            loss = 0.0
        else:
            loss = (before_mover - after_mover) / 100.0
        losses.append(loss)

        note = ""
        if "#" in san:
            note = ""
        elif loss >= 2.0:
            note = "??"
        elif loss >= 1.0:
            note = "?"
        elif loss <= -2.0:
            note = "!!"
        elif loss <= -0.5:
            note = "!"
        annotations.append(note)

    # Turning point: biggest absolute eval swing, but don't use the last 2 plies
    # so the turning-point replay stays distinct from the final position.
    candidates = list(range(1, len(moves) + 1))
    if len(moves) > 8:
        candidates = [i for i in candidates if i <= len(moves) - 2]
    best_ply = max(candidates, key=lambda i: abs(cps[i] - cps[i - 1]))
    best_loss = losses[best_ply - 1]

    before_board = positions[best_ply - 1]
    best_move = moves[best_ply - 1]
    captured = before_board.piece_at(best_move.to_square)
    badge, hook = _badge_for_move(sans[best_ply - 1], captured, best_loss)

    print(
        f"[stockfish] Done with {engine_name} depth {depth} | "
        f"turning point ply {best_ply} ({sans[best_ply - 1]}, loss {best_loss:+.1f})"
    )
    return {
        "engine": engine_name,
        "depth": depth,
        "evals": evals[1:],
        "losses": losses,
        "annotations": annotations,
        "climax_ply": best_ply,
        "climax_badge": badge,
        "climax_hook": hook,
    }
