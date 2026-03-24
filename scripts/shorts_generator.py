"""
YouTube Shorts Generator — repurpose long-form content into 60s vertical clips.
Extracts the hookiest parts of a script and renders 9:16 vertical video.
ALL FREE — uses Groq for extraction. Compatible with MoviePy v2.
"""

import json
import sys
from pathlib import Path

import requests
from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    ColorClip,
    concatenate_videoclips,
)

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    SHORTS_WIDTH,
    SHORTS_HEIGHT,
    SHORTS_FPS,
    GROQ_API_KEY,
    SCRIPT_MODEL,
    VIDEO_DIR,
    AUDIO_DIR,
)


def extract_hook_for_short(script: dict) -> dict:
    """Extract the most engaging 45-60 seconds of content for a Short using Groq."""
    full_text = script.get("hook", "") + "\n"
    for section in script.get("sections", [])[:3]:
        full_text += section.get("narration", "") + "\n"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": SCRIPT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Extract the most hook-worthy 60-second segment from a script for a YouTube Short. Return ONLY valid JSON.",
            },
            {
                "role": "user",
                "content": f"""Pick the section that would make someone stop scrolling.
Return JSON: {{"narration": "the 45-60 second narration", "visual_keywords": ["keyword1", "keyword2"]}}

Script:
{full_text}""",
            },
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    data = response.json()
    text = data["choices"][0]["message"]["content"]
    return json.loads(text)


def create_short(
    audio_path: Path,
    subtitles: list,
    footage_files: list,
    output_path: Path,
) -> Path:
    """Create a vertical 9:16 YouTube Short."""

    narration = AudioFileClip(str(audio_path))
    duration = min(narration.duration, 59.0)
    narration = narration.subclipped(0, duration)

    if footage_files:
        clip_dur = duration / max(len(footage_files), 1)
        clips = []
        for fp in footage_files:
            try:
                c = VideoFileClip(str(fp))
                if c.w / c.h > SHORTS_WIDTH / SHORTS_HEIGHT:
                    c = c.resized(height=SHORTS_HEIGHT)
                    x_center = c.w // 2
                    c = c.cropped(
                        x1=x_center - SHORTS_WIDTH // 2,
                        x2=x_center + SHORTS_WIDTH // 2,
                    )
                else:
                    c = c.resized(width=SHORTS_WIDTH)
                    y_center = c.h // 2
                    c = c.cropped(
                        y1=y_center - SHORTS_HEIGHT // 2,
                        y2=y_center + SHORTS_HEIGHT // 2,
                    )
                c = c.subclipped(0, min(c.duration, clip_dur))
                clips.append(c)
            except Exception:
                clips.append(
                    ColorClip((SHORTS_WIDTH, SHORTS_HEIGHT), (10, 10, 10), duration=clip_dur)
                )
        video = concatenate_videoclips(clips).subclipped(0, duration)
    else:
        video = ColorClip((SHORTS_WIDTH, SHORTS_HEIGHT), (10, 10, 10), duration=duration)

    sub_clips = []
    for sub in subtitles:
        if sub["end"] > duration:
            break
        dur = sub["end"] - sub["start"]
        if dur <= 0:
            continue
        try:
            txt = (
                TextClip(
                    text=sub["text"],
                    font_size=72,
                    color="white",
                    stroke_color="black",
                    stroke_width=4,
                    font="Arial",
                    method="caption",
                    size=(SHORTS_WIDTH - 100, None),
                    text_align="center",
                )
                .with_position(("center", "center"))
                .with_start(sub["start"])
                .with_duration(dur)
            )
            sub_clips.append(txt)
        except Exception:
            pass

    final = CompositeVideoClip([video] + sub_clips).with_audio(narration)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path),
        fps=SHORTS_FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="6000k",
        preset="medium",
    )

    final.close()
    narration.close()
    print(f"  Short saved: {output_path} ({duration:.1f}s)")
    return output_path


if __name__ == "__main__":
    print("Shorts generator ready. Use extract_hook_for_short() + create_short().")
