import re
from typing import List, Dict, Any

def generate_word_timestamps(segment_text: str, seg_start: float, seg_end: float) -> List[Dict[str, Any]]:
    """
    Interpolates or generates word-level timestamps within a segment timeframe [seg_start, seg_end].
    """
    words = [w for w in re.split(r'\s+', segment_text.strip()) if w]
    if not words:
        return []

    duration = max(0.2, seg_end - seg_start)
    word_duration = duration / len(words)

    word_items = []
    current_time = seg_start
    for i, w in enumerate(words):
        w_start = round(current_time, 2)
        w_end = round(min(seg_end, current_time + word_duration), 2)
        word_items.append({
            "word": w,
            "start": w_start,
            "end": w_end
        })
        current_time += word_duration

    return word_items

def clean_and_format_segments(raw_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cleans segment text, ensures start/end sanity, and generates word timestamps if missing.
    """
    processed = []
    for s in raw_segments:
        text = s.get("text", "").strip()
        # Clean HTML tags and repetitive linebreaks
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            continue

        start = round(float(s.get("start", 0.0)), 2)
        duration = float(s.get("duration", s.get("end", start + 3.0) - start))
        end = round(max(start + 0.5, start + duration), 2)

        words = s.get("words")
        if not words or len(words) == 0:
            words = generate_word_timestamps(text, start, end)

        processed.append({
            "start": start,
            "end": end,
            "text": text,
            "words": words
        })

    return processed
