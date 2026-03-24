"""
Thumbnail Generator — creates clickable YouTube thumbnails.
Dark, dramatic style with bold text overlays.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, THUMBNAIL_DIR, THUMBNAIL_FONT_SIZE


def create_thumbnail(
    text: str,
    background_image_path: Path = None,
    output_path: Path = None,
    style: str = "dark_mystery",
) -> Path:
    """Create a YouTube thumbnail with text overlay."""

    if background_image_path and Path(background_image_path).exists():
        img = Image.open(background_image_path)
        img = img.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)
    else:
        # Create a dark gradient background
        img = _create_gradient_bg()

    # Apply style
    if style == "dark_mystery":
        img = _apply_dark_style(img)
    elif style == "red_alert":
        img = _apply_red_style(img)

    # Add text
    img = _add_text_overlay(img, text)

    # Add vignette
    img = _add_vignette(img)

    # Save
    if output_path is None:
        safe_name = text.replace(" ", "_")[:30].lower()
        output_path = THUMBNAIL_DIR / f"thumb_{safe_name}.png"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), quality=95)
    print(f"  Thumbnail saved: {output_path}")
    return output_path


def _create_gradient_bg() -> Image.Image:
    """Create a dark gradient background."""
    img = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
    draw = ImageDraw.Draw(img)

    for y in range(THUMBNAIL_HEIGHT):
        ratio = y / THUMBNAIL_HEIGHT
        r = int(20 + ratio * 30)
        g = int(10 + ratio * 15)
        b = int(30 + ratio * 40)
        draw.line([(0, y), (THUMBNAIL_WIDTH, y)], fill=(r, g, b))

    return img


def _apply_dark_style(img: Image.Image) -> Image.Image:
    """Apply dark, moody color grading."""
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.5)

    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.4)

    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.6)

    return img


def _apply_red_style(img: Image.Image) -> Image.Image:
    """Apply red-tinted danger style."""
    img = _apply_dark_style(img)

    red_overlay = Image.new("RGB", img.size, (180, 20, 20))
    img = Image.blend(img, red_overlay, 0.15)

    return img


def _add_text_overlay(img: Image.Image, text: str) -> Image.Image:
    """Add bold text with outline to the thumbnail."""
    draw = ImageDraw.Draw(img)

    # Try to use a bold font, fall back to default
    font_size = THUMBNAIL_FONT_SIZE
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except (IOError, OSError):
            font = ImageFont.load_default()

    # Text wrapping
    text = text.upper()
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        test_text = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_text, font=font)
        if bbox[2] - bbox[0] > THUMBNAIL_WIDTH - 120:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    # Calculate total text height
    line_height = font_size + 10
    total_height = len(lines) * line_height
    y_start = (THUMBNAIL_HEIGHT - total_height) // 2

    # Draw text with outline
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (THUMBNAIL_WIDTH - text_width) // 2
        y = y_start + i * line_height

        # Black outline
        outline_width = 4
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                draw.text((x + dx, y + dy), line, fill=(0, 0, 0), font=font)

        # Yellow/white text
        draw.text((x, y), line, fill=(255, 255, 50), font=font)

    return img


def _add_vignette(img: Image.Image) -> Image.Image:
    """Add a subtle vignette effect."""
    vignette = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(vignette)

    center_x = THUMBNAIL_WIDTH // 2
    center_y = THUMBNAIL_HEIGHT // 2
    max_radius = max(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)

    for i in range(max_radius, 0, -1):
        brightness = int(255 * (i / max_radius))
        draw.ellipse(
            [center_x - i, center_y - i, center_x + i, center_y + i],
            fill=brightness,
        )

    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=100))

    # Apply vignette as alpha mask blend
    img_array = img.copy()
    black = Image.new("RGB", img.size, (0, 0, 0))
    img_array = Image.composite(img_array, black, vignette)

    return img_array


if __name__ == "__main__":
    create_thumbnail(
        "They Never Came Back",
        style="dark_mystery",
    )
    create_thumbnail(
        "FORBIDDEN HISTORY",
        style="red_alert",
    )
    print("Test thumbnails generated!")
