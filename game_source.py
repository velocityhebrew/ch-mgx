"""
Dynamic, effectively unlimited game source.

Primary source: Chess.com public API — active elite grandmasters, recent
monthly archives, filtered to long decisive standard games.

Fallback: the curated 30-game library in grandmaster_database.py.

No-repeat: every selected game ID is written to used_games.json. The GitHub
workflow commits that file back to the repository, so future runs skip it.
"""

import os
import io
import re
import json
import time
import random
import datetime

import requests
import chess
import chess.pgn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

USED_FILE = os.path.join(BASE_DIR, "used_games.json")
LEADERBOARD_CACHE = os.path.join(CACHE_DIR, "leaderboards.json")
GM_CACHE = os.path.join(CACHE_DIR, "gm_players.json")

CHESSCOM = "https://api.chess.com/pub"
HEADERS = {
    "User-Agent": "ChessMagix/1.0 (daily chess video generator; contact: kreg9da@gmail.com)"
}

# 78-100 plies at the current narration pace is roughly 7-9.5 minutes.
MIN_PLIES = 78
MAX_PLIES = 100
MIN_RATING = 2400
MAX_PLAYERS = 12
MONTHS_BACK = 2
CACHE_SECONDS = 7 * 24 * 3600

# Try recognizable elite names first, then the live leaderboard.
PREFERRED_PLAYERS = [
    "MagnusCarlsen", "Hikaru", "Firouzja2003", "AnishGiri", "LevonAronian",
    "FabianoCaruana", "GMwso", "DanielNaroditsky", "Bigfish1995", "LyonBeast",
    "Parhamov", "Sina-Movahed", "NihalSarin", "ChristopherYoo", "GigaQuparadze",
    "GutovAndrey", "DenLaz", "HansOnTwitch", "Micki-taryan", "legendisback1",
]

PIECE_VALUES = {
    chess.PAWN: 5,
    chess.KNIGHT: 20,
    chess.BISHOP: 20,
    chess.ROOK: 30,
    chess.QUEEN: 50,
}

FALLBACK_PLAYERS = [
    "Hikaru", "MagnusCarlsen", "Firouzja2003", "AnishGiri", "LevonAronian",
    "FabianoCaruana", "GMwso", "DanielNaroditsky", "LyonBeast", "Bigfish1995",
    "Parhamov", "Sina-Movahed", "NihalSarin", "ChristopherYoo", "GigaQuparadze",
    "GutovAndrey", "DenLaz", "HansOnTwitch", "Micki-taryan", "legendisback1",
]


# ---------------------------------------------------------------------------
# Small JSON / HTTP helpers
# ---------------------------------------------------------------------------
def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path, data):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except Exception as e:
        print(f"[game_source] Could not write {os.path.basename(path)}: {e}")


def _cache_fresh(path):
    return os.path.exists(path) and (time.time() - os.path.getmtime(path) < CACHE_SECONDS)


def _get_json(url, timeout=30):
    last_err = None
    for attempt in range(3):
        try:
            res = requests.get(url, headers=HEADERS, timeout=timeout)
            if res.status_code == 200:
                return res.json()
            if res.status_code == 404:
                return None
            last_err = f"HTTP {res.status_code}"
        except Exception as e:
            last_err = e
        time.sleep(1.0 + attempt)
    print(f"[game_source] Request failed ({last_err}): {url}")
    return None


# ---------------------------------------------------------------------------
# Active players / GM titles
# ---------------------------------------------------------------------------
def _with_preferred(players):
    ordered = list(PREFERRED_PLAYERS)
    for name in players:
        if name not in ordered:
            ordered.append(name)
    return ordered


def get_active_players():
    """Top active rapid + blitz players from Chess.com leaderboards."""
    if _cache_fresh(LEADERBOARD_CACHE):
        cached = _read_json(LEADERBOARD_CACHE, {})
        players = cached.get("players", [])
        if players:
            return _with_preferred(players)

    data = _get_json(f"{CHESSCOM}/leaderboards")
    players = []
    if data:
        for key in ("live_rapid", "live_blitz"):
            for entry in data.get(key, [])[:50]:
                name = entry.get("username") or entry.get("player_id")
                if name and name not in players:
                    players.append(name)

    if not players:
        players = list(FALLBACK_PLAYERS)
        print("[game_source] Leaderboard unavailable; using fallback player list.")
    else:
        _write_json(LEADERBOARD_CACHE, {"players": players})
    return _with_preferred(players)


def get_gm_set():
    """Lower-case set of Chess.com GM usernames (for the 'GM ' prefix)."""
    if _cache_fresh(GM_CACHE):
        cached = _read_json(GM_CACHE, {})
        players = cached.get("players", [])
        if players:
            return {p.lower() for p in players}

    data = _get_json(f"{CHESSCOM}/titled/GM", timeout=45)
    players = data.get("players", []) if data else []
    if players:
        _write_json(GM_CACHE, {"players": players})
        return {p.lower() for p in players}

    print("[game_source] GM title list unavailable; continuing without titles.")
    return set()


def recent_months(count=MONTHS_BACK):
    today = datetime.date.today()
    months = []
    year, month = today.year, today.month
    for _ in range(count):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return months


def _seed():
    run_num = os.environ.get("GITHUB_RUN_NUMBER", "")
    try:
        run_part = int(run_num) * 1000003
    except ValueError:
        run_part = 0
    return run_part + datetime.date.today().toordinal() * 7919


# ---------------------------------------------------------------------------
# Game history (no repeats)
# ---------------------------------------------------------------------------
def load_used():
    data = _read_json(USED_FILE, {"games": []})
    return set(data.get("games", []))


def mark_used(game_id):
    data = _read_json(USED_FILE, {"games": []})
    games = [g for g in data.get("games", []) if g != game_id]
    games.append(game_id)
    data["games"] = games[-1000:]
    _write_json(USED_FILE, data)


# ---------------------------------------------------------------------------
# PGN helpers
# ---------------------------------------------------------------------------
def opening_name(eco_url, eco_code=""):
    if eco_url:
        slug = eco_url.rstrip("/").split("/")[-1]
        slug = slug.split("...")[0]
        slug = re.sub(r"-\d+\..*$", "", slug)
        slug = slug.replace("-", " ").strip()
        if slug:
            return slug[:70]
    return eco_code or "Grandmaster Opening"


def clean_pgn(game):
    exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
    return game.accept(exporter)


def analyse_climax(game):
    """Pick the most dramatic move and build the broadcast badge/hook."""
    board = chess.Board()
    scored = []
    total = 0
    for _ in game.mainline_moves():
        total += 1

    for ply, move in enumerate(game.mainline_moves(), 1):
        try:
            san = board.san(move)
        except Exception:
            san = move.uci()

        captured = board.piece_at(move.to_square)
        score = 0.0
        if "#" in san:
            score += 100
        elif "+" in san:
            score += 8
        if "x" in san:
            score += 10 + PIECE_VALUES.get(captured.piece_type, 0) if captured else 10
        if "=" in san:
            score += 40
        if san in ("O-O", "O-O-O"):
            score += 2
        score += 15.0 * (ply / max(1, total))

        board.push(move)
        scored.append({
            "ply": ply,
            "score": score,
            "san": san,
            "captured": captured.piece_type if captured else None,
            "is_check": "+" in san and "#" not in san,
            "is_mate": "#" in san,
            "is_promo": "=" in san,
        })

    if not scored:
        return {
            "climax_ply": 1,
            "climax_badge": "!! TACTICAL BLOW",
            "climax_hook": "THE MOVE THAT CHANGED EVERYTHING?!",
        }

    start = max(0, int(len(scored) * 0.25))
    pool = scored[start:]
    best = max(pool, key=lambda item: item["score"])

    # Don't make the turning-point replay identical to the final position.
    if best["ply"] >= len(scored) - 1 and len(scored) > 6:
        earlier = scored[start:-2]
        if earlier:
            best = max(earlier, key=lambda item: item["score"])

    if best["is_mate"]:
        badge, hook = "!! CHECKMATE", "THE FINAL BLOW?!"
    elif best["captured"] == chess.QUEEN:
        badge, hook = "!! QUEEN CAPTURE", "THE QUEEN CAPTURE THAT DECIDED IT?!"
    elif best["is_promo"]:
        badge, hook = "!! PROMOTION POWER", "A NEW QUEEN CHANGES EVERYTHING?!"
    elif best["is_check"]:
        badge, hook = "!! TACTICAL CHECK", "THE CHECK THAT TURNED THE GAME?!"
    elif best["captured"]:
        badge, hook = "!! TACTICAL CAPTURE", "CAN YOU SEE WHY THIS CAPTURE WINS?!"
    else:
        badge, hook = "!! TACTICAL BLOW", "THE MOVE THAT CHANGED EVERYTHING?!"

    return {
        "climax_ply": best["ply"],
        "climax_badge": badge,
        "climax_hook": hook,
    }


# ---------------------------------------------------------------------------
# Chess.com archive
# ---------------------------------------------------------------------------
def fetch_archive(player, year, month):
    url = f"{CHESSCOM}/player/{player}/games/{year}/{month:02d}"
    data = _get_json(url)
    games = data.get("games", []) if data else []
    print(f"[game_source] {player} {year}-{month:02d}: {len(games)} games")
    time.sleep(0.3)
    return games


def _game_candidates(games, time_classes, used, gm_set):
    candidates = []
    for raw in games:
        if not raw.get("rated") or raw.get("rules") != "chess":
            continue
        if raw.get("time_class") not in time_classes:
            continue
        if not raw.get("pgn"):
            continue

        pgn_text = raw["pgn"]
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        if game is None or game.errors:
            continue

        result = game.headers.get("Result", "")
        if result not in ("1-0", "0-1"):
            continue

        termination = (game.headers.get("Termination") or "").lower()
        if "abort" in termination or "double forfeit" in termination:
            continue

        try:
            plies = len(list(game.mainline_moves()))
        except Exception:
            continue
        if not (MIN_PLIES <= plies <= MAX_PLIES):
            continue

        try:
            white_elo = int(game.headers.get("WhiteElo", "0"))
            black_elo = int(game.headers.get("BlackElo", "0"))
        except ValueError:
            continue
        if white_elo < MIN_RATING or black_elo < MIN_RATING:
            continue

        game_id = "chesscom_" + (
            raw.get("uuid") or raw.get("url", "").rstrip("/").split("/")[-1]
        )
        if game_id in used:
            continue

        candidates.append((raw, game, plies, game_id))
    return candidates


def build_game_info(raw, game, plies, game_id, gm_set):
    white = game.headers.get("White", "White")
    black = game.headers.get("Black", "Black")
    white_elo = game.headers.get("WhiteElo", "2800")
    black_elo = game.headers.get("BlackElo", "2800")
    opening = opening_name(game.headers.get("ECOUrl") or raw.get("eco"), game.headers.get("ECO"))

    time_class = (raw.get("time_class") or "rapid").title()
    event = f"Chess.com Elite {time_class}"
    theme = f"{opening} • Tactical Masterclass"
    climax = analyse_climax(game)
    pgn = clean_pgn(game)

    def titled(name):
        return f"GM {name}" if name.lower() in gm_set else name

    return {
        "id": game_id,
        "source": "chess.com",
        "title": f"{white} vs {black}: {opening}",
        "white_name": titled(white),
        "black_name": titled(black),
        "white_rating": str(white_elo),
        "black_rating": str(black_elo),
        "event": event,
        "opening": opening,
        "theme": theme,
        "climax_ply": climax["climax_ply"],
        "climax_badge": climax["climax_badge"],
        "climax_hook": climax["climax_hook"],
        "pgn": pgn,
        "plies": plies,
        "url": raw.get("url", ""),
        "time_class": raw.get("time_class", ""),
    }


def fetch_dynamic_game(seed=None):
    """Fetch a fresh, long, decisive elite game. Returns None on failure."""
    seed = _seed() if seed is None else seed
    rng = random.Random(seed)
    used = load_used()
    players = get_active_players()
    if not players:
        return None

    gm_set = get_gm_set()
    months = recent_months()
    preferred = [p for p in players if p in PREFERRED_PLAYERS]
    others = [p for p in players if p not in PREFERRED_PLAYERS]
    rng.shuffle(preferred)
    rng.shuffle(others)
    attempt_pool = preferred[:6] + others[:max(0, MAX_PLAYERS - 6)]
    attempts = 0

    for time_classes in (("rapid", "classical"), ("blitz",)):
        for player in attempt_pool:
            for year, month in months:
                games = fetch_archive(player, year, month)
                attempts += 1
                candidates = _game_candidates(games, time_classes, used, gm_set)
                if not candidates:
                    continue

                candidates.sort(key=lambda item: item[3])
                raw, game, plies, game_id = candidates[rng.randrange(len(candidates))]
                info = build_game_info(raw, game, plies, game_id, gm_set)
                mark_used(game_id)
                print(
                    f"[game_source] Selected dynamic game: {info['white_name']} vs "
                    f"{info['black_name']} | {info['event']} | {plies} plies | {game_id}"
                )
                return info

            if attempts >= MAX_PLAYERS * MONTHS_BACK:
                break
        if attempts >= MAX_PLAYERS * MONTHS_BACK * 2:
            break

    print("[game_source] No qualifying dynamic game found.")
    return None


# ---------------------------------------------------------------------------
# Curated fallback
# ---------------------------------------------------------------------------
def _select_curated(seed):
    from grandmaster_database import GRANDMASTER_GAMES

    rng = random.Random(seed)
    used = load_used()
    candidates = []
    for game in GRANDMASTER_GAMES:
        try:
            parsed = chess.pgn.read_game(io.StringIO(game["pgn"]))
            plies = len(list(parsed.mainline_moves())) if parsed else 0
        except Exception:
            plies = 0
        candidates.append((plies, game))

    long_games = [item for item in candidates if item[0] >= 74]
    pool = long_games or candidates
    available = [
        item for item in pool
        if f"curated_{item[1]['id']}" not in used
    ] or pool

    plies, chosen = rng.choice(sorted(available, key=lambda item: item[1]["id"]))
    mark_used(f"curated_{chosen['id']}")
    info = dict(chosen)
    info["source"] = "curated"
    info["plies"] = plies
    print(f"[game_source] Selected curated fallback: {info['title']} ({plies} plies)")
    return info


def select_game(requested_id=None):
    """Main entry point used by the daily pipeline."""
    if requested_id:
        from grandmaster_database import get_game_of_the_day
        return get_game_of_the_day(requested_id)

    mode = os.getenv("GAME_SOURCE", "auto").strip().lower()
    seed = _seed()

    if mode in ("auto", "dynamic"):
        try:
            game = fetch_dynamic_game(seed)
            if game:
                return game
        except Exception as e:
            print(f"[game_source] Dynamic source error: {e}")

    if mode == "dynamic":
        print("[game_source] Dynamic mode requested but unavailable; using curated fallback.")

    return _select_curated(seed)
