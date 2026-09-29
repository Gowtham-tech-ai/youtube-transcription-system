import logging
from typing import List, Dict, Any

import argostranslate.translate


logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Supported languages
# ------------------------------------------------------------

SUPPORTED_LANGUAGES = {
    "en": "English",
    "te": "Telugu (తెలుగు)",
    "hi": "Hindi (हिन्दी)",
    "es": "Spanish (Español)",
    "fr": "French (Français)",
    "de": "German (Deutsch)",
    "zh-CN": "Chinese (Simplified)",
    "ja": "Japanese (日本語)",
    "ar": "Arabic (العربية)",
    "ta": "Tamil (தமிழ்)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ml": "Malayalam (മലയാളം)",
    "pt": "Portuguese (Português)",
    "ru": "Russian (Русский)",
    "ko": "Korean (한국어)",
    "it": "Italian (Italiano)",
}


# ------------------------------------------------------------
# Argos-supported local models
# ------------------------------------------------------------

ARGOS_LANGUAGE_CODES = {
    "en": "en",
    "hi": "hi",
    "es": "es",
    "fr": "fr",
    "de": "de",
}


# ------------------------------------------------------------
# Language helpers
# ------------------------------------------------------------

def normalize_language_code(language: str) -> str:
    """
    Normalize language codes used by the application.
    """

    if not language:
        return "en"

    language = language.strip()

    language_map = {
        "zh": "zh-CN",
        "zh-cn": "zh-CN",
        "zh_cn": "zh-CN",
        "en-us": "en",
        "en_us": "en",
    }

    return language_map.get(
        language.lower(),
        language,
    )


def _get_argos_code(language: str) -> str:
    """
    Convert application language code to Argos language code.
    """

    normalized = normalize_language_code(language)

    if normalized not in ARGOS_LANGUAGE_CODES:
        raise ValueError(
            f"Argos translation model is not configured for "
            f"language: {normalized}"
        )

    return ARGOS_LANGUAGE_CODES[normalized]


# ------------------------------------------------------------
# Translation
# ------------------------------------------------------------

def translate_segments(
    segments: List[Dict[str, Any]],
    target_language: str,
    source_language: str = "en",
) -> List[Dict[str, Any]]:
    """
    Translate transcript segments using Argos Translate.

    Argos Translate runs locally using installed language models.

    Features:
    - No API key required
    - No Google Translate rate limit
    - Works offline after model installation
    - Preserves segment timestamps
    - Preserves segment order
    - Does not silently mark failed translation as successful
    """

    if not segments:
        return []

    source_language = normalize_language_code(source_language)
    target_language = normalize_language_code(target_language)

    logger.info(
        "Starting local Argos translation: %s -> %s | segments=%d",
        source_language,
        target_language,
        len(segments),
    )

    # --------------------------------------------------------
    # No translation required
    # --------------------------------------------------------

    if source_language.lower() == target_language.lower():
        logger.info(
            "Source and target languages are identical. "
            "Skipping translation."
        )

        return [
            _preserve_segment(segment)
            for segment in segments
        ]

    # --------------------------------------------------------
    # Validate source language
    # --------------------------------------------------------

    if source_language not in ARGOS_LANGUAGE_CODES:
        raise ValueError(
            f"Argos does not support source language: "
            f"{source_language}"
        )

    # --------------------------------------------------------
    # Validate target language
    # --------------------------------------------------------

    if target_language not in ARGOS_LANGUAGE_CODES:
        raise ValueError(
            f"Argos translation model is not installed/configured "
            f"for target language: {target_language}"
        )

    argos_source = _get_argos_code(source_language)
    argos_target = _get_argos_code(target_language)

    # --------------------------------------------------------
    # Verify translation model
    # --------------------------------------------------------

    try:
        translation = (
            argostranslate.translate.get_translation_from_codes(
                argos_source,
                argos_target,
            )
        )

    except Exception as exc:
        logger.error(
            "Could not load Argos translation model "
            "%s -> %s: %s",
            argos_source,
            argos_target,
            exc,
        )

        raise RuntimeError(
            f"Argos translation model is not available for "
            f"{source_language} -> {target_language}. "
            f"Install the required Argos language model."
        ) from exc

    if translation is None:
        raise RuntimeError(
            f"No Argos translation model found for "
            f"{source_language} -> {target_language}."
        )

    logger.info(
        "Argos translation model loaded: %s -> %s",
        source_language,
        target_language,
    )

    translated_segments: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # Translate each segment locally
    # --------------------------------------------------------

    for index, segment in enumerate(segments, start=1):

        original_text = str(
            segment.get("text", "")
        ).strip()

        # Empty segment
        if not original_text:
            translated_segments.append(
                _create_translated_segment(
                    segment,
                    "",
                )
            )
            continue

        logger.debug(
            "Translating segment %d/%d",
            index,
            len(segments),
        )

        try:
            translated_text = translation.translate(
                original_text
            )

            if translated_text is None:
                raise RuntimeError(
                    "Argos returned None"
                )

            translated_text = str(
                translated_text
            ).strip()

            if not translated_text:
                raise RuntimeError(
                    "Argos returned empty translation"
                )

            translated_segments.append(
                _create_translated_segment(
                    segment,
                    translated_text,
                )
            )

        except Exception as exc:

            logger.error(
                "Translation failed for segment %d/%d: %s",
                index,
                len(segments),
                exc,
            )

            # IMPORTANT:
            # Do NOT silently use the original English text.
            # Raise the error so the API can report a real failure.
            raise RuntimeError(
                f"Translation failed for segment {index}: "
                f"{exc}"
            ) from exc

    logger.info(
        "Translation completed successfully: "
        "%d segments -> %s",
        len(translated_segments),
        target_language,
    )

    return translated_segments


# ------------------------------------------------------------
# Segment helpers
# ------------------------------------------------------------

def _create_translated_segment(
    segment: Dict[str, Any],
    translated_text: str,
) -> Dict[str, Any]:
    """
    Create translated segment while preserving timestamps.
    """

    return {
        "start": segment.get(
            "start",
            0.0,
        ),
        "end": segment.get(
            "end",
            0.0,
        ),
        "text": translated_text,
        "words": [],
    }


def _preserve_segment(
    segment: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Preserve a segment when translation is unnecessary.
    """

    return {
        "start": segment.get(
            "start",
            0.0,
        ),
        "end": segment.get(
            "end",
            0.0,
        ),
        "text": segment.get(
            "text",
            "",
        ),
        "words": segment.get(
            "words",
            [],
        ),
    }