"""Build the animated, color-coded space hero for the profile README."""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "hero-space.webp"
FONT = ROOT / "assets" / "fonts" / "Orbitron[wght].ttf"
WIDTH, HEIGHT = 1800, 620
FRAME_COUNT, FRAME_MS = 40, 100
SEED = 741903

# This sequence follows the project reel's color order.
STAR_COLORS = [
    "#F47B72", "#F39F65", "#F39F65", "#D5D968", "#A5D77A",
    "#7BD29B", "#67C8B5", "#6DBDDB", "#A38CE8",
]


def rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def tracked_text(draw: ImageDraw.ImageDraw, text: str, center: int, top: int,
                 font: ImageFont.FreeTypeFont, fill: tuple[int, int, int, int], spacing: int) -> None:
    widths = [draw.textlength(char, font=font) for char in text]
    x = center - (sum(widths) + spacing * (len(text) - 1)) / 2
    for char, width in zip(text, widths):
        draw.text((round(x), top), char, font=font, fill=fill)
        x += width + spacing


def make_background() -> tuple[Image.Image, list[tuple[int, int, int, int, int]]]:
    image = Image.new("RGBA", (WIDTH, HEIGHT))
    pixels = image.load()
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        color = (7 + round(t * 4), 11 + round(t * 5), 24 + round(t * 12), 255)
        for x in range(WIDTH):
            pixels[x, y] = color

    left, right, cy = 105, WIDTH - 105, 128
    centers = [round(left + i * (right - left) / (len(STAR_COLORS) - 1)) for i in range(len(STAR_COLORS))]

    # Restrained colored haze keeps the row atmospheric without photo-like clutter.
    haze = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    haze_draw = ImageDraw.Draw(haze)
    for cx, color_hex in zip(centers, STAR_COLORS):
        color = rgb(color_hex)
        haze_draw.ellipse((cx - 112, cy - 84, cx + 112, cy + 84), fill=(*color, 19))
    image.alpha_composite(haze.filter(ImageFilter.GaussianBlur(48)))

    # A fine, low-contrast line ties the colored stars into one constellation.
    line = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    line_draw = ImageDraw.Draw(line)
    for i in range(len(centers) - 1):
        a, b = rgb(STAR_COLORS[i]), rgb(STAR_COLORS[i + 1])
        mixed = tuple(round((x + y) / 2) for x, y in zip(a, b))
        line_draw.line((centers[i], cy, centers[i + 1], cy), fill=(*mixed, 62), width=2)
    image.alpha_composite(line)

    # Sparse pinpoint stars make the background read as space while preserving calm.
    rng = random.Random(SEED)
    dust = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    dust_draw = ImageDraw.Draw(dust)
    twinkles = []
    for _ in range(145):
        x, y = rng.randrange(24, WIDTH - 24), rng.randrange(18, HEIGHT - 18)
        radius = rng.choice((1, 1, 1, 2))
        base_alpha = rng.randrange(50, 135)
        phase = rng.random()
        tint = rng.choice(((190, 213, 255), (224, 229, 247), (190, 238, 232)))
        dust_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*tint, base_alpha))
        twinkles.append((x, y, radius, base_alpha, phase, tint))
    image.alpha_composite(dust)

    # A faint center wash keeps the wordmark clear against the points of light.
    shade = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    shade_draw = ImageDraw.Draw(shade)
    shade_draw.rounded_rectangle((280, 232, WIDTH - 280, 516), radius=120, fill=(5, 9, 21, 72))
    image.alpha_composite(shade.filter(ImageFilter.GaussianBlur(70)))

    font = ImageFont.truetype(str(FONT), 132)
    axes = font.get_variation_axes()
    if axes:
        font.set_variation_by_axes([620] + [axis["default"] for axis in axes[1:]])
    subtitle_font = ImageFont.truetype(str(FONT), 30)
    text = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text)
    tracked_text(text_draw, "Esia", WIDTH // 2, 275, font, (245, 248, 255, 255), 7)
    tracked_text(text_draw, "systems, robotics, engineering", WIDTH // 2, 430,
                 subtitle_font, (198, 213, 238, 255), 3)
    image.alpha_composite(text)
    return image, twinkles


def render_frame(background: Image.Image, twinkles: list[tuple[int, int, int, int, float, tuple[int, int, int]]], frame_index: int) -> Image.Image:
    frame = background.copy()
    draw = ImageDraw.Draw(frame)
    phase_t = frame_index / FRAME_COUNT

    # Small stars breathe very gently, like a slow exposure shimmer.
    for x, y, radius, base_alpha, phase, tint in twinkles:
        alpha = round(base_alpha * (0.78 + 0.22 * math.sin(2 * math.pi * (phase_t + phase))))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*tint, alpha))

    left, right, cy = 105, WIDTH - 105, 128
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for index, color_hex in enumerate(STAR_COLORS):
        cx = round(left + index * (right - left) / (len(STAR_COLORS) - 1))
        color = rgb(color_hex)
        pulse = (1 + math.sin(2 * math.pi * (phase_t * 2 - index / len(STAR_COLORS)))) / 2
        radius = 13 + round(pulse * 5)
        alpha = 24 + round(pulse * 28)
        glow_draw.ellipse((cx - radius * 2, cy - radius * 2, cx + radius * 2, cy + radius * 2),
                          fill=(*color, alpha))
    frame.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12)))

    points = ImageDraw.Draw(frame)
    for index, color_hex in enumerate(STAR_COLORS):
        cx = round(left + index * (right - left) / (len(STAR_COLORS) - 1))
        color = rgb(color_hex)
        pulse = (1 + math.sin(2 * math.pi * (phase_t * 2 - index / len(STAR_COLORS)))) / 2
        ray = 7 + round(pulse * 4)
        points.line((cx - ray, cy, cx + ray, cy), fill=(*color, 130), width=1)
        points.line((cx, cy - ray, cx, cy + ray), fill=(*color, 130), width=1)
        points.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(*color, 255))
        points.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=(246, 249, 255, 255))
    return frame.convert("RGB")


def main() -> None:
    background, twinkles = make_background()
    frames = [render_frame(background, twinkles, i) for i in range(FRAME_COUNT)]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUTPUT,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        quality=88,
        method=4,
        lossless=False,
    )
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
