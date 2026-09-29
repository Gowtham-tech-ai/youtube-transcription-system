import os
import logging
from typing import List, Dict, Any, Tuple, Optional

from youtube_transcript_api import YouTubeTranscriptApi

from app.pipeline.text_processor import clean_and_format_segments


logger = logging.getLogger(__name__)


# ============================================================
# YouTube Caption Transcription
# ============================================================

def fetch_youtube_captions(
    video_id: str,
) -> Tuple[bool, List[Dict[str, Any]], str]:
    """
    Fetch available YouTube captions.

    Priority:
    1. English manually-created/available transcript
    2. English auto-generated transcript
    3. First available transcript

    Returns:
        (
            success,
            transcript_segments,
            detected_language
        )
    """

    try:
        # ----------------------------------------------------
        # IMPORTANT:
        # Current youtube-transcript-api requires an instance.
        # ----------------------------------------------------

        ytt_api = YouTubeTranscriptApi()

        transcript_list = ytt_api.list(video_id)

        transcript = None

        # ----------------------------------------------------
        # Try English first
        # ----------------------------------------------------

        try:
            transcript = transcript_list.find_transcript(
                [
                    "en",
                    "en-US",
                    "en-GB",
                ]
            )

            logger.info(
                "English YouTube transcript found for %s",
                video_id,
            )

        except Exception:
            logger.info(
                "English transcript not found for %s. "
                "Searching for another available transcript.",
                video_id,
            )

        # ----------------------------------------------------
        # Fall back to first available transcript
        # ----------------------------------------------------

        if transcript is None:

            try:
                transcript = next(
                    iter(transcript_list)
                )

            except StopIteration:

                logger.info(
                    "No YouTube transcripts available for %s",
                    video_id,
                )

                return (
                    False,
                    [],
                    "en",
                )

        # ----------------------------------------------------
        # Fetch transcript
        # ----------------------------------------------------

        raw_data = transcript.fetch()

        lang_code = getattr(
            transcript,
            "language_code",
            "en",
        )

        segments: List[
            Dict[str, Any]
        ] = []

        # ----------------------------------------------------
        # Convert FetchedTranscript snippets
        # ----------------------------------------------------

        for item in raw_data:

            # Current API returns snippet objects.
            # Support both object-style and dict-style data
            # for compatibility with older versions.
            if hasattr(item, "text"):

                text = getattr(
                    item,
                    "text",
                    "",
                )

                start = getattr(
                    item,
                    "start",
                    0.0,
                )

                duration = getattr(
                    item,
                    "duration",
                    0.0,
                )

            else:

                text = item.get(
                    "text",
                    "",
                )

                start = item.get(
                    "start",
                    0.0,
                )

                duration = item.get(
                    "duration",
                    0.0,
                )

            start = float(
                start or 0.0
            )

            duration = float(
                duration or 0.0
            )

            segments.append(
                {
                    "start": start,
                    "duration": duration,
                    "end": start + duration,
                    "text": str(text or "").strip(),
                }
            )

        # ----------------------------------------------------
        # Validate result
        # ----------------------------------------------------

        if not segments:

            logger.warning(
                "YouTube transcript returned no usable "
                "segments for %s",
                video_id,
            )

            return (
                False,
                [],
                lang_code,
            )

        formatted = clean_and_format_segments(
            segments
        )

        logger.info(
            "Successfully fetched YouTube captions: "
            "video=%s language=%s segments=%d",
            video_id,
            lang_code,
            len(formatted),
        )

        return (
            True,
            formatted,
            lang_code,
        )

    except Exception as e:

        logger.warning(
            "YouTube transcript API failed for %s: %s. "
            "Falling back to Whisper.",
            video_id,
            e,
        )

        return (
            False,
            [],
            "en",
        )


# ============================================================
# Whisper Transcription
# ============================================================

def transcribe_audio_whisper(
    audio_path: str,
    model_name: str = "openai/whisper-tiny",
) -> List[Dict[str, Any]]:
    """
    Transcribe preprocessed audio using Hugging Face Whisper.

    CPU is used when CUDA is unavailable.
    """

    if not os.path.exists(audio_path):

        logger.warning(
            "Audio file %s not found for Whisper",
            audio_path,
        )

        return []

    try:

        import torch
        from transformers import pipeline

        # ----------------------------------------------------
        # Select device
        # ----------------------------------------------------

        if torch.cuda.is_available():

            device = "cuda:0"

            logger.info(
                "CUDA available. Using GPU for Whisper."
            )

        else:

            device = "cpu"

            logger.info(
                "CUDA unavailable. Using CPU for Whisper."
            )

        logger.info(
            "Loading Whisper pipeline (%s) on %s...",
            model_name,
            device,
        )

        # ----------------------------------------------------
        # Create ASR pipeline
        # ----------------------------------------------------

        asr = pipeline(
            "automatic-speech-recognition",
            model=model_name,
            chunk_length_s=30,
            return_timestamps=True,
            device=device,
        )

        # ----------------------------------------------------
        # Run transcription
        # ----------------------------------------------------

        result = asr(audio_path)

        chunks = result.get(
            "chunks",
            [],
        )

        if not chunks:

            logger.warning(
                "Whisper returned no timestamped chunks "
                "for %s",
                audio_path,
            )

            return []

        raw_segments: List[
            Dict[str, Any]
        ] = []

        # ----------------------------------------------------
        # Convert Whisper chunks
        # ----------------------------------------------------

        for chunk in chunks:

            timestamp = chunk.get(
                "timestamp",
                (0.0, 0.0),
            )

            if not timestamp:
                continue

            start = timestamp[0]

            end = timestamp[1]

            # Whisper can sometimes return None
            # for the ending timestamp.
            if start is None:
                start = 0.0

            if end is None:
                end = start + 3.0

            start = float(start)
            end = float(end)

            text = chunk.get(
                "text",
                "",
            )

            text = str(
                text or ""
            ).strip()

            if not text:
                continue

            raw_segments.append(
                {
                    "start": start,
                    "end": end,
                    "text": text,
                }
            )

        if not raw_segments:

            logger.warning(
                "Whisper produced no usable transcript "
                "segments."
            )

            return []

        formatted = clean_and_format_segments(
            raw_segments
        )

        logger.info(
            "Whisper transcription completed: "
            "segments=%d",
            len(formatted),
        )

        return formatted

    except Exception as e:

        logger.error(
            "Whisper inference error: %s",
            e,
            exc_info=True,
        )

        return []


# ============================================================
# Main Transcription Pipeline
# ============================================================

def get_transcription(
    video_id: str,
    audio_path: Optional[str] = None,
) -> Tuple[
    List[Dict[str, Any]],
    str,
]:
    """
    Main transcription pipeline.

    Priority:

        YouTube captions
              ↓
        Whisper fallback
              ↓
        real failure

    No fake/demo transcript is generated.
    """

    logger.info(
        "Starting transcription for video %s",
        video_id,
    )

    # --------------------------------------------------------
    # STEP 1: YouTube captions
    # --------------------------------------------------------

    success, segments, language = (
        fetch_youtube_captions(video_id)
    )

    if success and segments:

        logger.info(
            "Using YouTube captions for %s",
            video_id,
        )

        return (
            segments,
            language,
        )

    # --------------------------------------------------------
    # STEP 2: Whisper fallback
    # --------------------------------------------------------

    if audio_path and os.path.exists(audio_path):

        logger.info(
            "YouTube captions unavailable. "
            "Using Whisper for %s",
            video_id,
        )

        whisper_segments = (
            transcribe_audio_whisper(
                audio_path
            )
        )

        if whisper_segments:

            logger.info(
                "Using Whisper transcription for %s",
                video_id,
            )

            return (
                whisper_segments,
                "en",
            )

    # --------------------------------------------------------
    # STEP 3: Real failure
    # --------------------------------------------------------

    logger.error(
        "Transcription failed for video %s. "
        "No YouTube captions and Whisper produced "
        "no transcript.",
        video_id,
    )

    return (
        [],
        "en",
    )