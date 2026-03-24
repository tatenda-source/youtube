"""
Script Generator — generates narration scripts for Dark History / Rabbit Hole videos.
Uses OpenAI GPT-4o to create engaging, retention-optimized scripts.
"""

import json
import sys
from pathlib import Path
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import OPENAI_API_KEY, SCRIPT_MODEL, TARGET_VIDEO_LENGTH_MINUTES, WORDS_PER_MINUTE

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are an expert YouTube scriptwriter specializing in dark history,
mysteries, and rabbit hole content. You write scripts that are:

- Hook-heavy: First 10 seconds must be impossible to skip
- Conversational but authoritative — like a smart friend telling you something insane
- Full of "wait, it gets worse" moments to maintain retention
- Structured with mini-cliffhangers every 60-90 seconds
- Factually accurate but presented in the most compelling way possible

You write for faceless YouTube channels with narration over stock footage.

OUTPUT FORMAT:
Return a JSON object with:
{
  "title": "YouTube title (clickable but not clickbait)",
  "description": "YouTube description with keywords",
  "tags": ["tag1", "tag2", ...],
  "hook": "The first 2 sentences — the hook that stops the scroll",
  "sections": [
    {
      "section_title": "Section name (not shown in video, for organization)",
      "narration": "The actual narration text for this section",
      "visual_keywords": ["keyword1", "keyword2"] // for stock footage search
    }
  ],
  "thumbnail_text": "Short punchy text for thumbnail (2-5 words)"
}"""


def generate_script(topic: str, style: str = "documentary") -> dict:
    """Generate a full video script from a topic."""

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
- End with a mind-blowing conclusion or unresolved mystery"""

    response = client.chat.completions.create(
        model=SCRIPT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
    )

    script = json.loads(response.choices[0].message.content)
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
