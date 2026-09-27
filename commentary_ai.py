import urllib.request
import urllib.parse
import json

POLLINATIONS_BASE_URL = "https://text.pollinations.ai/"

def query_pollinations_ai(prompt: str, timeout: int = 8) -> str:
    """Queries Pollinations.ai free API for dynamic AI commentary."""
    try:
        url = POLLINATIONS_BASE_URL + urllib.parse.quote(prompt)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="ignore").strip()
            # Clean up response quotes
            text = text.strip('"\'')
            return text
    except Exception as e:
        print(f"[pollinations] Note: {e} - using tactical fallback")
        return ""

def get_dynamic_commentary(player_name: str, san_move: str, strategy: str, eval_score: str, fallback_text: str) -> str:
    """
    Generates dynamic grandmaster commentary using Pollinations AI,
    falling back to curated strategic text if unavailable.
    """
    prompt = (
        f"You are {player_name}, a 2850-rated Chess Grandmaster playing blitz. "
        f"You just played the move {san_move}. Strategy: {strategy}. Evaluation: {eval_score}. "
        f"In 1 to 2 sharp, intellectual, confident sentences, explain your move and its tactical threat. "
        f"No markdown, no bullet points, just spoken words."
    )
    
    generated = query_pollinations_ai(prompt)
    if generated and len(generated) > 20 and len(generated) < 260:
        return generated
    
    return fallback_text

if __name__ == "__main__":
    test_commentary = get_dynamic_commentary(
        player_name="GM Alexander",
        san_move="Nd5!!",
        strategy="Central Knight Sacrifice",
        eval_score="+1.8",
        fallback_text="Knight takes d5!! A thunderous positional sacrifice right in the center!"
    )
    print("Commentary Result:\n", test_commentary)
