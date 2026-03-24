"""
Script Generator — generates narration scripts for Dark History / Rabbit Hole videos.
Uses Groq (FREE) with Llama 3.3 70B for fast, high-quality scripts.
"""

import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import GROQ_API_KEY, SCRIPT_MODEL, TARGET_VIDEO_LENGTH_MINUTES, WORDS_PER_MINUTE

SYSTEM_PROMPT = """You are an expert YouTube scriptwriter specializing in dark history,
mysteries, and rabbit hole content. You write scripts that are:

- Hook-heavy: First 10 seconds must be impossible to skip
- Conversational but authoritative — like a smart friend telling you something insane
- Full of "wait, it gets worse" moments to maintain retention
- Structured with mini-cliffhangers every 60-90 seconds
- Factually accurate but presented in the most compelling way possible

You write for faceless YouTube channels with narration over stock footage.

OUTPUT FORMAT — respond with ONLY valid JSON, no markdown:
{
  "title": "YouTube title (clickable but not clickbait)",
  "description": "YouTube description with keywords",
  "tags": ["tag1", "tag2"],
  "hook": "The first 2 sentences — the hook that stops the scroll",
  "sections": [
    {
      "section_title": "Section name (not shown in video, for organization)",
      "narration": "The actual narration text for this section",
      "visual_keywords": ["keyword1", "keyword2"]
    }
  ],
  "thumbnail_text": "Short punchy text for thumbnail (2-5 words)"
}"""


def generate_script(topic: str, style: str = "documentary") -> dict:
    """Generate a full video script from a topic using Groq."""

    target_words = TARGET_VIDEO_LENGTH_MINUTES * WORDS_PER_MINUTE

    user_prompt = f"""Create a YouTube script about: {topic}

Style: {style}
Target length: ~{target_words} words of narration (about {TARGET_VIDEO_LENGTH_MINUTES} minutes)

Break it into 6-10 sections. Each section should have its own mini-arc.
Include visual keywords for each section so we can find matching stock footage.

Remember:
- Start with an absolute banger hook
- Every section should end with something that makes viewers need to hear the next part
- Include specific dates, names, and details for credibility
- End with a mind-blowing conclusion or unresolved mystery

Respond with ONLY the JSON object, no markdown code blocks."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": SCRIPT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 8192,
        "response_format": {"type": "json_object"},
    }

    # Retry with backoff for rate limits
    for attempt in range(3):
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 429:
            wait = 15 * (attempt + 1)
            print(f"  Rate limited, waiting {wait}s (attempt {attempt + 1}/3)...")
            time.sleep(wait)
            continue
        response.raise_for_status()
        break
    else:
        raise Exception("Groq API rate limit — try again in a minute")

    data = response.json()
    text = data["choices"][0]["message"]["content"]

    script = json.loads(text)
    return script


def save_script(script: dict, output_path: Path) -> Path:
    """Save the generated script to a JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(script, f, indent=2)
    return output_path


def get_full_narration(script: dict) -> str:
    """Extract the full narration text from a script."""
    parts = [script.get("hook", "")]
    for section in script.get("sections", []):
        parts.append(section.get("narration", ""))
    return "\n\n".join(parts)


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "The Dyatlov Pass Incident"
    print(f"Generating script for: {topic}")

    script = generate_script(topic)
    narration = get_full_narration(script)
    word_count = len(narration.split())

    out_path = save_script(script, Path("output") / f"{topic.replace(' ', '_').lower()}_script.json")

    print(f"Title: {script['title']}")
    print(f"Word count: {word_count} (~{word_count // WORDS_PER_MINUTE} min)")
    print(f"Sections: {len(script['sections'])}")
    print(f"Saved to: {out_path}")
