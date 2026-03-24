"""
Video Assembler — stitches everything together into a final video.
Combines stock footage, narration audio, subtitles, and background music.
Compatible with MoviePy v2.
"""

import sys
from pathlib import Path

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
    concatenate_audioclips,
    ColorClip,
)

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    FPS,
    VIDEO_DIR,
    BG_MUSIC_VOLUME,
    SUBTITLE_FONT_SIZE,
    SUBTITLE_FONT_COLOR,
    SUBTITLE_STROKE_COLOR,
    SUBTITLE_STROKE_WIDTH,
    SUBTITLE_POSITION,
)


def load_and_resize_clip(video_path: Path, target_duration: float) -> VideoFileClip:
    """Load a video clip, resize to target dimensions, and trim/loop to target duration."""
    clip = VideoFileClip(str(video_path))
    clip = clip.resized((VIDEO_WIDTH, VIDEO_HEIGHT))

    if clip.duration > target_duration:
        clip = clip.subclipped(0, target_duration)
    elif clip.duration < target_duration:
        loops_needed = int(target_duration / clip.duration) + 1
        clip = concatenate_videoclips([clip] * loops_needed).subclipped(0, target_duration)

    return clip


def create_footage_sequence(footage_files: list, total_duration: float):
    """Create a sequence of stock footage clips that fills the total duration."""
    if not footage_files:
        return ColorClip(
            size=(VIDEO_WIDTH, VIDEO_HEIGHT),
            color=(10, 10, 10),
            duration=total_duration,
        )

    clip_duration = total_duration / len(footage_files)
    clips = []

    for footage_path in footage_files:
        try:
            clip = load_and_resize_clip(footage_path, clip_duration)
            clips.append(clip)
        except Exception as e:
            print(f"  Warning: Failed to load {footage_path}: {e}")
            clips.append(
                ColorClip(
                    size=(VIDEO_WIDTH, VIDEO_HEIGHT),
                    color=(10, 10, 10),
                    duration=clip_duration,
                )
            )

    return concatenate_videoclips(clips)


def create_subtitle_clips(subtitles: list) -> list:
    """Create TextClip overlays for each subtitle."""
    subtitle_clips = []

    for sub in subtitles:
        duration = sub["end"] - sub["start"]
        if duration <= 0:
            continue

        try:
            pos = ("center", "center") if SUBTITLE_POSITION == "center" else ("center", 0.85)
            txt_clip = (
                TextClip(
                    text=sub["text"],
                    font_size=SUBTITLE_FONT_SIZE,
                    color=SUBTITLE_FONT_COLOR,
                    stroke_color=SUBTITLE_STROKE_COLOR,
                    stroke_width=SUBTITLE_STROKE_WIDTH,
                    font="Arial",
                    method="caption",
                    size=(VIDEO_WIDTH - 200, None),
                    text_align="center",
                )
                .with_position(pos)
                .with_start(sub["start"])
                .with_duration(duration)
            )
            subtitle_clips.append(txt_clip)
        except Exception as e:
            print(f"  Warning: Failed to create subtitle clip: {e}")

    return subtitle_clips


def assemble_video(
    footage_files: list,
    audio_path: Path,
    subtitles: list,
    output_path: Path,
    bg_music_path: Path = None,
) -> Path:
    """Assemble the final video from all components."""
    print("Assembling video...")

    # Load narration audio
    narration = AudioFileClip(str(audio_path))
    total_duration = narration.duration
    print(f"  Video duration: {total_duration:.1f}s")

    # Create footage sequence
    print("  Building footage sequence...")
    video = create_footage_sequence(footage_files, total_duration)

    # Create subtitle overlays
    print("  Adding subtitles...")
    subtitle_clips = create_subtitle_clips(subtitles)

    # Composite video + subtitles
    final_video = CompositeVideoClip([video] + subtitle_clips)

    # Build audio track
    audio_tracks = [narration]
    if bg_music_path and bg_music_path.exists():
        print("  Adding background music...")
        bg_music = AudioFileClip(str(bg_music_path))
        if bg_music.duration < total_duration:
            loops = int(total_duration / bg_music.duration) + 1
            bg_music = concatenate_audioclips([bg_music] * loops)
        bg_music = bg_music.subclipped(0, total_duration).with_volume_scaled(BG_MUSIC_VOLUME)
        audio_tracks.append(bg_music)

    final_audio = CompositeAudioClip(audio_tracks)
    final_video = final_video.with_audio(final_audio)

    # Render
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  Rendering to {output_path.name}...")
    final_video.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",
        preset="medium",
        threads=4,
    )

    # Cleanup
    final_video.close()
    narration.close()

    print(f"  Done! Video saved: {output_path}")
    return output_path


if __name__ == "__main__":
    print("Video assembler ready. Use assemble_video() with your components.")
