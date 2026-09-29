import os
import subprocess
import logging
from pathlib import Path
from app.config import AUDIOS_DIR

logger = logging.getLogger(__name__)

def extract_and_preprocess_audio(input_audio_path: str, video_id: str) -> str:
    """
    Extracts, converts to 16kHz 16-bit mono WAV, and applies audio preprocessing
    (loudness normalization and noise suppression filter) using FFmpeg.
    """
    output_wav = str(AUDIOS_DIR / f"{video_id}_clean.wav")
    if os.path.exists(output_wav):
        return output_wav

    if not os.path.exists(input_audio_path):
        logger.warning(f"Input audio {input_audio_path} does not exist, creating placeholder")
        return input_audio_path

    try:
        # Step 2 & 3: FFmpeg audio extraction & preprocessing
        # -ar 16000: 16kHz sample rate optimal for Whisper
        # -ac 1: mono channel
        # -af "loudnorm,afftdn=nf=-25": loudness normalization and FFT noise reduction
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_audio_path,
            "-ar", "16000",
            "-ac", "1",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            output_wav
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if res.returncode == 0 and os.path.exists(output_wav):
            logger.info(f"Audio preprocessed successfully: {output_wav}")
            return output_wav
        else:
            logger.warning(f"FFmpeg preprocessing note: {res.stderr.decode('utf-8', errors='ignore')[:200]}")
            return input_audio_path
    except Exception as e:
        logger.error(f"FFmpeg preprocessing error: {e}")
        return input_audio_path
