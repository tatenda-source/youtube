"""
Text-to-Speech Engine — converts narration scripts to audio.
Supports OpenAI TTS, ElevenLabs, and Google TTS.
"""

import sys
from pathlib import Path
from pydub import AudioSegment

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    AUDIO_DIR,
    TTS_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_TTS_VOICE,
    OPENAI_TTS_MODEL,
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
)


def tts_openai(text: str, output_path: Path, voice: str = None) -> Path:
    """Generate speech using OpenAI TTS."""
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    voice = voice or OPENAI_TTS_VOICE

    response = client.audio.speech.create(
        model=OPENAI_TTS_MODEL,
        voice=voice,
        input=text,
        response_format="mp3",
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response.stream_to_file(str(output_path))
    return output_path


def tts_elevenlabs(text: str, output_path: Path, voice_id: str = None) -> Path:
    """Generate speech using ElevenLabs API."""
    import requests

    voice_id = voice_id or ELEVENLABS_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.6,
            "similarity_boost": 0.85,
        },
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)
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
    "openai": tts_openai,
    "elevenlabs": tts_elevenlabs,
    "google": tts_google,
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
        segment = AudioSegment.from_mp3(str(audio_file))
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
