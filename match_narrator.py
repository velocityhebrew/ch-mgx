import os
import asyncio
import edge_tts
import soundfile as sf

VOICES = {
    "White": "en-US-GuyNeural",         # GM Alexander - Energetic, assertive tactician
    "Black": "en-US-ChristopherNeural"  # GM Victor - Deep, analytical, calculating
}

class ChessNarrator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_dialogue(self, clip_id: str, player: str, text: str) -> str:
        voice = VOICES.get(player, "en-US-GuyNeural")
        clip_path = os.path.join(self.output_dir, f"{clip_id}_{player.lower()}.mp3")
        
        # Call edge-tts
        comm = edge_tts.Communicate(text, voice)
        await comm.save(clip_path)
        
        return clip_path

    def get_audio_duration(self, audio_path: str) -> float:
        try:
            data, fs = sf.read(audio_path)
            return len(data) / fs
        except Exception:
            return 3.5
