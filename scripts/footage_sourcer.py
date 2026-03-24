"""
Stock Footage Sourcer — fetches relevant stock videos from Pexels API.
Uses visual keywords from the script to find matching footage.
"""

import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    PEXELS_API_KEY,
    STOCK_DIR,
    PEXELS_VIDEO_ORIENTATION,
    PEXELS_VIDEO_SIZE,
    MIN_CLIP_DURATION,
    MAX_CLIP_DURATION,
)


def search_pexels_videos(query: str, per_page: int = 5) -> list:
    """Search Pexels for stock videos matching a query."""
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "per_page": per_page,
        "orientation": PEXELS_VIDEO_ORIENTATION,
        "size": PEXELS_VIDEO_SIZE,
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    videos = []

    for video in data.get("videos", []):
        duration = video.get("duration", 0)
        if duration < MIN_CLIP_DURATION:
            continue

        # Get the best quality video file
        video_files = video.get("video_files", [])
        best_file = None
        for vf in video_files:
            if vf.get("quality") == "hd" and vf.get("width", 0) >= 1280:
                best_file = vf
                break
        if not best_file and video_files:
            best_file = video_files[0]

        if best_file:
            videos.append({
                "id": video["id"],
                "url": best_file["link"],
                "width": best_file.get("width", 0),
                "height": best_file.get("height", 0),
                "duration": duration,
                "query": query,
            })

    return videos


def download_video(url: str, output_path: Path) -> Path:
    """Download a video file from a URL."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return output_path


def fetch_footage_for_section(keywords: list, section_idx: int, clips_per_section: int = 3) -> list:
    """Fetch stock footage for a script section using its visual keywords."""
    downloaded = []

    for keyword in keywords[:3]:  # max 3 keywords per section
        print(f"  Searching: '{keyword}'...")
        try:
            videos = search_pexels_videos(keyword, per_page=clips_per_section)
        except requests.RequestException as e:
            print(f"  Warning: Search failed for '{keyword}': {e}")
            continue

        for j, video in enumerate(videos[:clips_per_section]):
            filename = STOCK_DIR / f"section_{section_idx:02d}_{keyword.replace(' ', '_')}_{j}.mp4"

            if filename.exists():
                print(f"  Already downloaded: {filename.name}")
                downloaded.append(filename)
                continue

            try:
                download_video(video["url"], filename)
                downloaded.append(filename)
                print(f"  Downloaded: {filename.name} ({video['duration']}s)")
            except requests.RequestException as e:
                print(f"  Warning: Download failed: {e}")

        # Rate limiting — Pexels allows 200 requests/hour
        time.sleep(1)

    return downloaded


def fetch_all_footage(script: dict) -> dict:
    """Fetch stock footage for all sections of a script.
    Returns dict mapping section index to list of video paths.
    """
    footage_map = {}

    # Fetch for hook — use visually interesting keywords, avoid generic dark clips
    hook_keywords = ["old documents", "ancient ruins", "foggy forest"]
    print("Fetching hook footage...")
    footage_map[-1] = fetch_footage_for_section(hook_keywords, 0)

    # Fetch for each section
    for i, section in enumerate(script.get("sections", [])):
        keywords = section.get("visual_keywords", [])
        if not keywords:
            keywords = [section.get("section_title", "history documentary")]
        print(f"Fetching footage for section {i + 1}: {section.get('section_title', '')}...")
        footage_map[i] = fetch_footage_for_section(keywords, i + 1)

    total = sum(len(v) for v in footage_map.values())
    print(f"\nTotal clips downloaded: {total}")
    return footage_map


if __name__ == "__main__":
    # Quick test
    print("Testing Pexels search...")
    results = search_pexels_videos("dark forest mystery", per_page=3)
    for r in results:
        print(f"  Found: {r['duration']}s - {r['url'][:80]}...")
