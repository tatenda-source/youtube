"""
Text-to-Speech Engine — converts narration scripts to audio.
Uses edge-tts (FREE, high quality Microsoft Edge voices) as primary.
Google gTTS as fallback (also free).
"""

import asyncio
import sys
from pathlib import Path

from pydub import AudioSegment

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import AUDIO_DIR, TTS_PROVIDER, EDGE_TTS_VOICE


def tts_edge(text: str, output_path: Path, voice: str = None) -> Path:
    """Generate speech using edge-tts (free, high quality)."""
    import edge_tts

    voice = voice or EDGE_TTS_VOICE
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    async def _generate():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))

    asyncio.run(_generate())
    return output_path


def tts_google(text: str, output_path: Path) -> Path:
    """Generate speech using Google gTTS (free, no API key needed)."""
    from gtts import gTTS

    tts = gTTS(text=text, lang="en", slow=False)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tts.save(str(output_path))
    return output_path


TTS_PROVIDERS = {
    "edge": tts_edge,
    "google": tts_google,
}

# Available edge-tts voices for dark/narrator content:
EDGE_VOICES = {
    "guy": "en-US-GuyNeural",          # Deep male — best for dark history
    "eric": "en-US-EricNeural",         # Authoritative male
    "davis": "en-US-DavisNeural",       # Calm narrator
    "tony": "en-US-TonyNeural",         # Dramatic male
    "andrew": "en-US-AndrewNeural",     # Documentary style
    "brian": "en-US-BrianNeural",       # News anchor style
    "jenny": "en-US-JennyNeural",       # Female narrator
    "aria": "en-US-AriaNeural",         # Female dramatic
}


def generate_audio(text: str, output_path: Path, provider: str = None) -> Path:
    """Generate audio using the configured TTS provider."""
    provider = provider or TTS_PROVIDER
    tts_func = TTS_PROVIDERS.get(provider)
    if not tts_func:
        raise ValueError(f"Unknown TTS provider: {provider}. Use: {list(TTS_PROVIDERS.keys())}")
    return tts_func(text, Path(output_path))


def generate_section_audio(sections: list, base_name: str, provider: str = None) -> list:
    """Generate separate audio files for each script section.
    Returns list of audio file paths.
    """
    audio_files = []
    for i, section in enumerate(sections):
        narration = section.get("narration", "")
        if not narration.strip():
            continue
        filename = AUDIO_DIR / f"{base_name}_section_{i:02d}.mp3"
        generate_audio(narration, filename, provider)
        audio_files.append(filename)
        print(f"  Generated audio: {filename.name}")
    return audio_files


def combine_audio(audio_files: list, output_path: Path, pause_ms: int = 500) -> Path:
    """Combine multiple audio files into one with pauses between them."""
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=pause_ms)

    for i, audio_file in enumerate(audio_files):
        segment = AudioSegment.from_file(str(audio_file))
        combined += segment
        if i < len(audio_files) - 1:
            combined += pause

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.export(str(output_path), format="mp3")
    print(f"  Combined audio: {output_path.name} ({len(combined) / 1000:.1f}s)")
    return output_path


def get_audio_duration(audio_path: Path) -> float:
    """Get duration of an audio file in seconds."""
    audio = AudioSegment.from_file(str(audio_path))
    return len(audio) / 1000.0


if __name__ == "__main__":
    test_text = "In 1959, nine hikers ventured into the Ural Mountains. None of them came back alive."
    out = AUDIO_DIR / "test_narration.mp3"
    generate_audio(test_text, out)
    duration = get_audio_duration(out)
    print(f"Generated: {out} ({duration:.1f}s)")
