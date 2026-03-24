"""
YouTube Shorts Generator — repurpose long-form content into 60s vertical clips.
Extracts the hookiest parts of a script and renders 9:16 vertical video.
"""

import json
import sys
from pathlib import Path

from moviepy.editor import (
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
    OPENAI_API_KEY,
    VIDEO_DIR,
    AUDIO_DIR,
)


def extract_hook_for_short(script: dict) -> dict:
    """Extract the most engaging 45-60 seconds of content for a Short."""
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    full_text = script.get("hook", "") + "\n"
    for section in script.get("sections", [])[:3]:
        full_text += section.get("narration", "") + "\n"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """Extract the most hook-worthy 60-second segment from this script
for a YouTube Short. Pick the section that would make someone stop scrolling.
Return JSON: {"narration": "the 45-60 second narration", "visual_keywords": ["keyword1", "keyword2"]}""",
            },
            {"role": "user", "content": full_text},
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def create_short(
    audio_path: Path,
    subtitles: list,
    footage_files: list,
    output_path: Path,
) -> Path:
    """Create a vertical 9:16 YouTube Short."""

    narration = AudioFileClip(str(audio_path))
    duration = min(narration.duration, 59.0)  # Shorts max 60s
    narration = narration.subclip(0, duration)

    # Create vertical footage
    if footage_files:
        clip_dur = duration / max(len(footage_files), 1)
        clips = []
        for fp in footage_files:
            try:
                c = VideoFileClip(str(fp))
                # Center-crop to vertical
                if c.w / c.h > SHORTS_WIDTH / SHORTS_HEIGHT:
                    c = c.resize(height=SHORTS_HEIGHT)
                    x_center = c.w // 2
                    c = c.crop(
                        x1=x_center - SHORTS_WIDTH // 2,
                        x2=x_center + SHORTS_WIDTH // 2,
                    )
                else:
                    c = c.resize(width=SHORTS_WIDTH)
                    y_center = c.h // 2
                    c = c.crop(
                        y1=y_center - SHORTS_HEIGHT // 2,
                        y2=y_center + SHORTS_HEIGHT // 2,
                    )
                c = c.subclip(0, min(c.duration, clip_dur))
                clips.append(c)
            except Exception:
                clips.append(
                    ColorClip((SHORTS_WIDTH, SHORTS_HEIGHT), (10, 10, 10), duration=clip_dur)
                )
        video = concatenate_videoclips(clips, method="compose").subclip(0, duration)
    else:
        video = ColorClip((SHORTS_WIDTH, SHORTS_HEIGHT), (10, 10, 10), duration=duration)

    # Add larger subtitles for vertical format
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
                    sub["text"],
                    fontsize=72,
                    color="white",
                    stroke_color="black",
                    stroke_width=4,
                    font="Arial-Bold",
                    method="caption",
                    size=(SHORTS_WIDTH - 100, None),
                    align="center",
                )
                .set_position(("center", "center"))
                .set_start(sub["start"])
                .set_duration(dur)
            )
            sub_clips.append(txt)
        except Exception:
            pass

    final = CompositeVideoClip([video] + sub_clips).set_audio(narration)

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
