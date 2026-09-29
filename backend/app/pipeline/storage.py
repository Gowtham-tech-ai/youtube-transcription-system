import os
import math
from typing import List, Dict, Any
from app.config import SUBTITLES_DIR

def format_timestamp_srt(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"

def format_timestamp_vtt(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{msecs:03d}"

def generate_srt(segments: List[Dict[str, Any]]) -> str:
    lines = []
    for idx, seg in enumerate(segments, start=1):
        start = format_timestamp_srt(seg.get("start", 0.0))
        end = format_timestamp_srt(seg.get("end", 0.0))
        text = seg.get("text", "").strip()
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)

def generate_vtt(segments: List[Dict[str, Any]]) -> str:
    lines = ["WEBVTT\n"]
    for idx, seg in enumerate(segments, start=1):
        start = format_timestamp_vtt(seg.get("start", 0.0))
        end = format_timestamp_vtt(seg.get("end", 0.0))
        text = seg.get("text", "").strip()
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)

def generate_txt(segments: List[Dict[str, Any]]) -> str:
    return "\n".join([seg.get("text", "").strip() for seg in segments if seg.get("text")])

def save_subtitles(video_id: str, lang: str, segments: List[Dict[str, Any]]):
    srt_path = SUBTITLES_DIR / f"{video_id}_{lang}.srt"
    vtt_path = SUBTITLES_DIR / f"{video_id}_{lang}.vtt"
    txt_path = SUBTITLES_DIR / f"{video_id}_{lang}.txt"

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(generate_srt(segments))

    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write(generate_vtt(segments))

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(generate_txt(segments))

    return {
        "srt": str(srt_path),
        "vtt": str(vtt_path),
        "txt": str(txt_path)
    }
