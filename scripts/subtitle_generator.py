"""
Subtitle Generator — creates word-level timed subtitles.
Uses estimation from text + audio duration (fully free, no API needed).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SUBTITLE_DIR, MAX_WORDS_PER_SUBTITLE


def estimate_timestamps(text: str, audio_duration: float) -> list:
    """Estimate word timestamps based on audio duration.
    Distributes words evenly across the duration.
    """
    words_list = text.split()
    if not words_list:
        return []

    time_per_word = audio_duration / len(words_list)
    words = []

    for i, word in enumerate(words_list):
        words.append({
            "word": word,
            "start": round(i * time_per_word, 3),
            "end": round((i + 1) * time_per_word, 3),
        })

    return words


def group_words_into_subtitles(words: list, max_words: int = None) -> list:
    """Group individual words into subtitle chunks."""
    max_words = max_words or MAX_WORDS_PER_SUBTITLE
    subtitles = []

    for i in range(0, len(words), max_words):
        chunk = words[i : i + max_words]
        subtitle = {
            "text": " ".join(w["word"] for w in chunk),
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
        }
        subtitles.append(subtitle)

    return subtitles


def generate_srt(subtitles: list, output_path: Path) -> Path:
    """Generate an SRT subtitle file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for i, sub in enumerate(subtitles, 1):
        start = _format_srt_time(sub["start"])
        end = _format_srt_time(sub["end"])
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(sub["text"])
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path


def _format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_subtitles(audio_path: Path, text: str, audio_duration: float) -> list:
    """Generate subtitles using timestamp estimation."""
    print("  Estimating subtitle timestamps...")
    words = estimate_timestamps(text, audio_duration)
    subtitles = group_words_into_subtitles(words)
    print(f"  Generated {len(subtitles)} subtitle groups")
    return subtitles


def save_subtitles(subtitles: list, output_path: Path) -> Path:
    """Save subtitles as both SRT and JSON."""
    srt_path = generate_srt(subtitles, output_path.with_suffix(".srt"))

    json_path = output_path.with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump(subtitles, f, indent=2)

    print(f"  Saved {len(subtitles)} subtitles: {srt_path.name}")
    return srt_path


if __name__ == "__main__":
    test_text = "In 1959 nine hikers ventured into the Ural Mountains. None of them came back alive. What happened on that mountain remains one of history's greatest unsolved mysteries."
    subs = group_words_into_subtitles(
        estimate_timestamps(test_text, 15.0)
    )
    out = SUBTITLE_DIR / "test_subs"
    save_subtitles(subs, out)
    for s in subs:
        print(f"  [{s['start']:.1f}-{s['end']:.1f}] {s['text']}")
