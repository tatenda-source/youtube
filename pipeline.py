#!/usr/bin/env python3
"""
Faceless YouTube Video Pipeline — Dark History / Rabbit Holes

Usage:
    python pipeline.py "The Dyatlov Pass Incident"
    python pipeline.py "MK Ultra CIA Mind Control" --style red_alert
    python pipeline.py "The Lost Colony of Roanoke" --tts google --no-footage

One command: topic → finished video + thumbnail ready to upload.
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from config import VIDEO_DIR, AUDIO_DIR, SUBTITLE_DIR, THUMBNAIL_DIR, MUSIC_DIR
from scripts.script_generator import generate_script, save_script, get_full_narration
from scripts.tts_engine import generate_audio, generate_section_audio, combine_audio, get_audio_duration
from scripts.footage_sourcer import fetch_all_footage
from scripts.subtitle_generator import generate_subtitles, save_subtitles
from scripts.video_assembler import assemble_video
from scripts.thumbnail_generator import create_thumbnail


def slugify(text: str) -> str:
    """Convert topic to a safe filename slug."""
    return text.lower().replace(" ", "_").replace("'", "")[:50]


def run_pipeline(
    topic: str,
    tts_provider: str = None,
    thumbnail_style: str = "dark_mystery",
    skip_footage: bool = False,
    skip_video: bool = False,
):
    """Run the full video pipeline from topic to finished video."""
    slug = slugify(topic)
    print("=" * 60)
    print(f"  FACELESS YOUTUBE PIPELINE")
    print(f"  Topic: {topic}")
    print("=" * 60)

    # ─── Step 1: Generate Script ────────────────────────────
    print("\n[1/6] Generating script...")
    script = generate_script(topic)
    script_path = save_script(script, Path("output") / f"{slug}_script.json")
    narration = get_full_narration(script)
    word_count = len(narration.split())
    print(f"  Title: {script['title']}")
    print(f"  Words: {word_count} | Sections: {len(script['sections'])}")

    # ─── Step 2: Generate Audio ─────────────────────────────
    print("\n[2/6] Generating narration audio...")
    audio_files = generate_section_audio(script["sections"], slug, tts_provider)

    # Generate hook audio separately
    if script.get("hook"):
        hook_audio = AUDIO_DIR / f"{slug}_hook.mp3"
        generate_audio(script["hook"], hook_audio, tts_provider)
        audio_files.insert(0, hook_audio)
        print(f"  Generated audio: {hook_audio.name}")

    # Combine all audio
    combined_audio = AUDIO_DIR / f"{slug}_full.mp3"
    combine_audio(audio_files, combined_audio)
    total_duration = get_audio_duration(combined_audio)
    print(f"  Total narration: {total_duration:.1f}s ({total_duration / 60:.1f} min)")

    # ─── Step 3: Generate Subtitles ─────────────────────────
    print("\n[3/6] Generating subtitles...")
    subtitles = generate_subtitles(combined_audio, narration, total_duration)
    sub_path = SUBTITLE_DIR / f"{slug}_subs"
    save_subtitles(subtitles, sub_path)

    # ─── Step 4: Fetch Stock Footage ────────────────────────
    footage_files = []
    if not skip_footage:
        print("\n[4/6] Fetching stock footage...")
        footage_map = fetch_all_footage(script)
        # Flatten footage map to a list
        for section_idx in sorted(footage_map.keys()):
            footage_files.extend(footage_map[section_idx])
        print(f"  Total clips: {len(footage_files)}")
    else:
        print("\n[4/6] Skipping footage (--no-footage)")

    # ─── Step 5: Assemble Video ─────────────────────────────
    if not skip_video:
        print("\n[5/6] Assembling video...")
        # Check for background music
        bg_music = None
        music_files = list(MUSIC_DIR.glob("*.mp3"))
        if music_files:
            bg_music = music_files[0]
            print(f"  Using background music: {bg_music.name}")

        output_video = VIDEO_DIR / f"{slug}.mp4"
        assemble_video(
            footage_files=footage_files,
            audio_path=combined_audio,
            subtitles=subtitles,
            output_path=output_video,
            bg_music_path=bg_music,
        )
    else:
        print("\n[5/6] Skipping video assembly (--no-video)")
        output_video = None

    # ─── Step 6: Generate Thumbnail ─────────────────────────
    print("\n[6/6] Generating thumbnail...")
    thumb_text = script.get("thumbnail_text", topic[:30])
    # Use first stock footage frame as background if available
    thumb_bg = footage_files[0] if footage_files else None
    thumbnail = create_thumbnail(
        text=thumb_text,
        output_path=THUMBNAIL_DIR / f"{slug}_thumb.png",
        style=thumbnail_style,
    )

    # ─── Summary ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE!")
    print("=" * 60)
    print(f"  Title:     {script['title']}")
    print(f"  Script:    {script_path}")
    print(f"  Audio:     {combined_audio}")
    print(f"  Subtitles: {sub_path}.srt")
    if output_video:
        print(f"  Video:     {output_video}")
    print(f"  Thumbnail: {thumbnail}")
    print(f"  Duration:  {total_duration / 60:.1f} min")
    print(f"\n  Description:\n  {script.get('description', 'N/A')}")
    print(f"\n  Tags: {', '.join(script.get('tags', []))}")
    print("=" * 60)

    return {
        "title": script["title"],
        "description": script.get("description", ""),
        "tags": script.get("tags", []),
        "script_path": str(script_path),
        "audio_path": str(combined_audio),
        "subtitle_path": f"{sub_path}.srt",
        "video_path": str(output_video) if output_video else None,
        "thumbnail_path": str(thumbnail),
        "duration_seconds": total_duration,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Faceless YouTube Video Pipeline — Dark History / Rabbit Holes"
    )
    parser.add_argument("topic", help="Video topic (e.g., 'The Dyatlov Pass Incident')")
    parser.add_argument("--tts", choices=["openai", "elevenlabs", "google"], help="TTS provider")
    parser.add_argument("--style", choices=["dark_mystery", "red_alert"], default="dark_mystery", help="Thumbnail style")
    parser.add_argument("--no-footage", action="store_true", help="Skip stock footage download")
    parser.add_argument("--no-video", action="store_true", help="Skip video assembly (script + audio only)")

    args = parser.parse_args()

    run_pipeline(
        topic=args.topic,
        tts_provider=args.tts,
        thumbnail_style=args.style,
        skip_footage=args.no_footage,
        skip_video=args.no_video,
    )


if __name__ == "__main__":
    main()
