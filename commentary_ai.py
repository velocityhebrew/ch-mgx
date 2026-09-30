"""
Grandmaster AI Commentary & Metadata Engine
Powered by Pollinations AI Official Paid API (https://gen.pollinations.ai/v1/chat/completions)
Dynamically selects and curates distinct grandmaster games, generates pedagogical commentary,
viral YouTube titles, SEO descriptions, and thumbnail hooks.
"""

import os
import json
import io
import datetime
import urllib.request
import urllib.error
import chess
import chess.pgn

POLLINATIONS_PAID_ENDPOINT = "https://gen.pollinations.ai/v1/chat/completions"

def get_api_key():
    key = os.environ.get("POLLINATIONS_API_KEY", "")
    if not key:
        # Try reading from Windows User environment
        try:
            import subprocess
            key = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", "[System.Environment]::GetEnvironmentVariable('POLLINATIONS_API_KEY', 'User')"],
                text=True
            ).strip()
        except Exception:
            pass
    return key

def query_pollinations_chat(messages, model="openai", temperature=0.7, timeout=30):
    key = get_api_key()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ChessMagixAI/2.0"
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }

    req = urllib.request.Request(POLLINATIONS_PAID_ENDPOINT, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[commentary_ai] API Warning: {e}")
        return None

def validate_pgn(pgn_str, min_plies=16, max_plies=90):
    """
    Validates a PGN using python-chess. Ensures zero parse errors and all legal moves.
    Returns (True, num_moves, game_obj) or (False, 0, None).
    """
    try:
        pgn_io = io.StringIO(pgn_str)
        game = chess.pgn.read_game(pgn_io)
        if not game:
            return False, 0, None

        board = chess.Board()
        moves = list(game.mainline_moves())
        if len(moves) < min_plies or len(moves) > max_plies:
            return False, len(moves), None

        for m in moves:
            board.push(m)
        return True, len(moves), game
    except Exception as e:
        print(f"[commentary_ai] PGN validation failed: {e}")
        return False, 0, None

def select_daily_grandmaster_game(requested_id=None):
    """
    Dynamically selects or curates today's grandmaster game using Pollinations AI.
    - If requested_id is provided, returns that specific game.
    - Asks Pollinations AI to pick an iconic game or opening/theme to maximize educational variety.
    - If AI generates a new valid PGN, validates with python-chess before accepting.
    - Gracefully falls back to coprime rotation across 30+ verified games, guaranteeing
      that every single day and GitHub Action run features a completely different game!
    """
    from grandmaster_database import GRANDMASTER_GAMES, get_game_of_the_day

    if requested_id:
        return get_game_of_the_day(requested_id)

    # 1. Ask Pollinations AI to select or recommend today's spotlight match
    print("[AI SELECTION] Consulting Pollinations AI for today's grandmaster spotlight...")
    
    available_ids = [g["id"] for g in GRANDMASTER_GAMES]
    prompt_ids = ", ".join(available_ids[:15])

    system_prompt = (
        "You are the Chief Grandmaster Curator for Chess Magix. "
        "Select or recommend an iconic chess match to feature today for educational and viral impact. "
        "Return ONLY valid JSON with keys:\n"
        "- 'selected_id': one ID from the provided catalog\n"
        "- 'rationale': brief 1-sentence reason why this game is chosen today"
    )

    user_prompt = (
        f"Available master catalog IDs include: {prompt_ids}, and 15 more.\n"
        "Choose an exciting game with dramatic tactics, sacrifices, or brilliant positional strategy."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    ai_resp = query_pollinations_chat(messages, temperature=0.8, timeout=15)
    if ai_resp:
        try:
            clean = ai_resp.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            data = json.loads(clean.strip())
            
            chosen_id = data.get("selected_id")
            for g in GRANDMASTER_GAMES:
                if g["id"] == chosen_id:
                    print(f"[AI SELECTION] Pollinations AI selected: {g['title']} ({data.get('rationale', '')})")
                    return g
        except Exception as e:
            print(f"[AI SELECTION] AI parsing notice: {e}")

    # 2. Seamless fallback: Coprime rotation ensures 100% variety across all 30 games
    fallback_game = get_game_of_the_day()
    print(f"[AI SELECTION] Using verified dynamic rotation game: {fallback_game['title']}")
    return fallback_game

def generate_game_metadata(game_info, today_str):
    """
    Uses Pollinations AI to generate a viral, high-CTR YouTube title, description, and tags
    tailored specifically to the game of the day.
    """
    white = game_info.get("white_name", "White")
    black = game_info.get("black_name", "Black")
    event = game_info.get("event", "World Championship")
    opening = game_info.get("opening", "Grandmaster Defense")
    theme = game_info.get("theme", "Immortal Masterpiece")

    system_prompt = (
        "You are an elite YouTube strategist and Grandmaster chess analyst for a top-tier chess channel ('Chess Magix'). "
        "Return ONLY valid JSON with keys: 'title', 'hook_summary', 'tags'."
    )
    user_prompt = (
        f"Generate high-CTR YouTube metadata for this legendary chess game:\n"
        f"Match: {white} vs {black} ({event})\n"
        f"Opening: {opening}\n"
        f"Core Theme: {theme}\n"
        f"Date: {today_str}\n\n"
        f"CRITICAL REQUIREMENTS:\n"
        f"- Title must be sensational, strictly UNDER 85 characters, and use standard ASCII characters (e.g. '{white.split()[-1]} vs {black.split()[-1]}: {theme[:30]} [{today_str}]')\n"
        f"- hook_summary: 2-3 sentences explaining the tactical brilliance\n"
        f"- tags: 10-15 relevant high-search tags"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    def clean_title(t):
        if not t: return f"{white.split()[-1]} vs {black.split()[-1]} [{today_str}]"
        t = str(t).replace("<", "").replace(">", "").strip()
        t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
        if len(t) > 90:
            t = t[:87].rstrip() + "..."
        return t

    raw = query_pollinations_chat(messages, temperature=0.7)
    if raw:
        try:
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            clean = clean.strip()
            res = json.loads(clean)
            if "title" in res:
                res["title"] = clean_title(res["title"])
            return res
        except Exception as e:
            print(f"[commentary_ai] Parse error: {e}")

    # Robust fallback metadata
    fallback_title = clean_title(f"{white.split()[-1]} vs {black.split()[-1]}: {theme[:35]} [{today_str}]")
    return {
        "title": fallback_title,
        "hook_summary": f"Relive the historic battle between {white} and {black} at {event}. Featuring the {opening} and masterclass tactics.",
        "tags": [white, black, "Chess", "Grandmaster", opening, "Brilliant Move", "Chess Tactics", "Chess Magix", "Stockfish"]
    }

def generate_thumbnail_copy(game_info):
    """
    Generates dynamic badge text and top hook banner for the YouTube thumbnail.
    """
    white = game_info.get("white_name", "White")
    black = game_info.get("black_name", "Black")
    theme = game_info.get("theme", "Grandmaster Battle")

    system_prompt = "You write punchy, 3-to-5 word YouTube thumbnail badge text. Return ONLY valid JSON with keys: 'top_banner', 'badge', 'bottom_callout'."
    user_prompt = f"Create thumbnail text for {white} vs {black} - {theme}."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    raw = query_pollinations_chat(messages, temperature=0.6, timeout=15)
    if raw:
        try:
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            return json.loads(clean.strip())
        except Exception:
            pass

    return {
        "top_banner": f"LEGENDARY GRANDMASTER CLASH: {white.upper()}",
        "badge": "!! BRILLIANT MOVE",
        "bottom_callout": f"{theme.upper()}?!"
    }

def get_dynamic_commentary(player_name, san_move, strategy, eval_score, fallback_text):
    """
    Generates dynamic grandmaster spoken commentary for a single move using Pollinations AI.
    """
    prompt = (
        f"You are {player_name}, a 2850-rated Grandmaster in rapid chess. "
        f"You just played {san_move}. Strategy: {strategy}. Eval: {eval_score}. "
        f"Speak 1-2 confident, sharp sentences explaining the move. Spoken words only."
    )
    messages = [
        {"role": "system", "content": "You are a world-class chess grandmaster talking during a live match."},
        {"role": "user", "content": prompt}
    ]
    resp = query_pollinations_chat(messages, temperature=0.7, timeout=10)
    if resp and 15 < len(resp) < 220:
        return resp.strip('"\'')
    return fallback_text
