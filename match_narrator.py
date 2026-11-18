import os
import re
import asyncio
import hashlib
import subprocess
import edge_tts
import soundfile as sf

# MultilingualNeural voices are Microsoft's most natural, conversational models.
VOICE_PROFILES = {
    "White": {
        "primary": "en-US-AndrewMultilingualNeural",   # warm, energetic play-by-play
        "fallbacks": ["en-US-GuyNeural", "en-US-ChristopherNeural"],
        "rate": "+6%", "pitch": "+2Hz",
    },
    "Black": {
        "primary": "en-US-BrianMultilingualNeural",    # deep, calm, analytical
        "fallbacks": ["en-US-ChristopherNeural", "en-GB-RyanNeural"],
        "rate": "+2%", "pitch": "-3Hz",
    },
    "Host": {
        "primary": "en-US-AvaMultilingualNeural",      # expressive presenter
        "fallbacks": ["en-US-JennyNeural", "en-US-AriaNeural"],
        "rate": "+5%", "pitch": "+0Hz",
    },
}

# Broadcast-style polish: rumble cut, presence boost, gentle compression, loudness normalize.
POLISH_FILTER = (
    "highpass=f=75,"
    "equalizer=f=2800:t=q:w=1.1:g=1.8,"
    "acompressor=threshold=-20dB:ratio=3:attack=12:release=160:makeup=2,"
    "loudnorm=I=-16:TP=-1.5:LRA=11"
)


def speech_text(text):
    """Clean written punctuation into natural spoken cadence."""
    t = text.replace("!!", "!").replace("?", "?").strip()
    t = t.replace("—", ", ").replace("–", ", ")
    t = t.replace("...", ". ").replace("..", ". ")
    t = re.sub(r"[\"'“”‘’]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


class ChessNarrator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    async def _synthesize(self, text, voice, rate, pitch, path):
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await comm.save(path)

    async def generate_dialogue(self, clip_id: str, player: str, text: str) -> str:
        profile = VOICE_PROFILES.get(player, VOICE_PROFILES["White"])
        clean = speech_text(text)
        digest = hashlib.md5(clean.encode("utf-8")).hexdigest()[:8]
        raw_path = os.path.join(self.output_dir, f"{clip_id}_{player.lower()}_{digest}_raw.mp3")
        final_path = os.path.join(self.output_dir, f"{clip_id}_{player.lower()}_{digest}.wav")
        if os.path.exists(final_path) and os.path.getsize(final_path) > 1000:
            return final_path

        voices = [profile["primary"]] + profile["fallbacks"]
        last_err = None
        for voice in voices:
            for attempt in range(3):
                try:
                    await self._synthesize(clean, voice, profile["rate"], profile["pitch"], raw_path)
                    if os.path.exists(raw_path) and os.path.getsize(raw_path) > 1000:
                        last_err = None
                        break
                except Exception as e:
                    last_err = e
                    await asyncio.sleep(1.0 + attempt)
            if last_err is None:
                break
        if last_err is not None:
            raise RuntimeError(f"TTS failed for {clip_id}: {last_err}")

        cmd = [
            "ffmpeg", "-y", "-i", raw_path,
            "-af", POLISH_FILTER,
            "-ar", "44100", "-ac", "1",
            final_path,
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0 or not os.path.exists(final_path):
            return raw_path
        try:
            os.remove(raw_path)
        except OSError:
            pass
        return final_path

    def get_audio_duration(self, audio_path: str) -> float:
        try:
            data, fs = sf.read(audio_path)
            return len(data) / fs
        except Exception:
            return 3.5