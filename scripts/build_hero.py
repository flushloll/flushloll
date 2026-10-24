"""Render the profile hero as a procedurally generated deep-space banner."""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "hero-space.png"
FONT = ROOT / "assets" / "fonts" / "Orbitron[wght].ttf"
WIDTH, HEIGHT = 1800, 620
SEED = 741903

# The order matches the project reel, including the shared amber for its two
# equally rated game projects.
STAR_COLORS = [
    "#F47B72", "#F39F65", "#F39F65", "#D5D968", "#A5D77A",
    "#7BD29B", "#67C8B5", "#6DBDDB", "#A38CE8",
]


def rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def cloud_noise(rng: random.Random) -> Image.Image:
    """Create layered, smooth noise to break up the nebula into dusty clouds."""
    fields = []
    for divisor, weight in ((7, 0.20), (14, 0.25), (28, 0.25), (56, 0.18), (112, 0.12)):
        size = (max(2, WIDTH // divisor), max(2, HEIGHT // divisor))
        small = Image.new("L", size)
        small.putdata([max(0, min(255, int(rng.gauss(128, 60)))) for _ in range(size[0] * size[1])])
        fields.append((small.resize((WIDTH, HEIGHT), Image.Resampling.BICUBIC), weight))
    field = Image.new("L", (WIDTH, HEIGHT), 128)
    for noise, weight in fields:
        field = Image.blend(field, noise, weight)
    return ImageEnhance.Contrast(field).enhance(2.0)


def add_nebula(image: Image.Image, noise: Image.Image) -> None:
    # Each softly overlapping cloud uses a color from the star progression.
    clouds = [
        (-0.05, 0.26, 0.25, 0.94, "#5D3D8A", 104),
        (0.17, 0.18, 0.42, 0.82, "#A7475E", 115),
        (0.38, 0.14, 0.63, 0.77, "#AB7045", 96),
        (0.57, 0.18, 0.82, 0.90, "#358675", 100),
        (0.75, 0.09, 1.05, 0.88, "#594B9C", 116),
        (0.24, 0.56, 0.78, 1.16, "#263C72", 74),
    ]
    for x0, y0, x1, y1, color, opacity in clouds:
        mask = Image.new("L", (WIDTH, HEIGHT), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((int(x0 * WIDTH), int(y0 * HEIGHT), int(x1 * WIDTH), int(y1 * HEIGHT)), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(100))
        textured = ImageChops.multiply(mask, noise)
        textured = ImageEnhance.Brightness(textured).enhance(opacity / 128)
        layer = Image.new("RGBA", (WIDTH, HEIGHT), (*rgb(color), 255))
        layer.putalpha(textured)
        image.alpha_composite(layer)

    # Fine dusty wisps add structure while leaving the title area readable.
    wisps = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(wisps)
    for i in range(13):
        x = int(WIDTH * (0.08 + i * 0.067))
        y = int(HEIGHT * (0.28 + 0.12 * math.sin(i * 0.83)))
        draw.ellipse((x - 250, y - 24, x + 250, y + 24), fill=(108, 120, 189, 20))
    image.alpha_composite(wisps.filter(ImageFilter.GaussianBlur(34)))


def draw_background_stars(image: Image.Image, rng: random.Random) -> None:
    stars = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(stars)
    for _ in range(1250):
        x, y = rng.randrange(WIDTH), rng.randrange(HEIGHT)
        radius = rng.choices((1, 2, 3), (0.78, 0.20, 0.02))[0]
        alpha = rng.randrange(38, 150) if radius == 1 else rng.randrange(50, 180)
        tint = rng.choice(((205, 220, 255), (255, 231, 214), (205, 235, 245), (228, 215, 255)))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*tint, alpha))
    image.alpha_composite(stars.filter(ImageFilter.GaussianBlur(0.45)))


def draw_feature_stars(image: Image.Image) -> None:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    left, right, cy = 105, WIDTH - 105, 128
    for index, color_hex in enumerate(STAR_COLORS):
        cx = round(left + index * (right - left) / (len(STAR_COLORS) - 1))
        color = rgb(color_hex)
        radius = (10, 11, 10, 9, 10, 9, 10, 11, 9)[index]

        # Layered colored corona with a compact white-hot stellar core.
        for factor, alpha in ((6.5, 9), (4.6, 16), (3.0, 28), (1.8, 58), (1.0, 150)):
            r = radius * factor
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*color, alpha))
        for half_width, alpha in ((radius * 4.2, 28), (radius * 2.6, 58), (radius * 1.5, 110)):
            draw.line((cx - half_width, cy, cx + half_width, cy), fill=(*color, alpha), width=1)
            draw.line((cx, cy - half_width, cx, cy + half_width), fill=(*color, alpha), width=1)
        core = max(4, round(radius * 0.46))
        draw.ellipse((cx - core, cy - core, cx + core, cy + core), fill=(*color, 255))
        draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=(255, 255, 255, 255))

    image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.8)))
    crisp = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(crisp)
    for index in range(len(STAR_COLORS)):
        cx = round(left + index * (right - left) / (len(STAR_COLORS) - 1))
        draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=(255, 255, 255, 255))
        draw.line((cx - 23, cy, cx + 23, cy), fill=(230, 239, 255, 150), width=1)
        draw.line((cx, cy - 23, cx, cy + 23), fill=(230, 239, 255, 150), width=1)
    image.alpha_composite(crisp.filter(ImageFilter.GaussianBlur(0.35)))


def tracked_text(draw: ImageDraw.ImageDraw, text: str, center: int, top: int,
                 font: ImageFont.FreeTypeFont, fill: tuple[int, int, int, int], spacing: int) -> None:
    widths = [draw.textlength(char, font=font) for char in text]
    x = center - (sum(widths) + spacing * (len(text) - 1)) / 2
    for char, width in zip(text, widths):
        draw.text((round(x), top), char, font=font, fill=fill, stroke_width=0)
        x += width + spacing


def add_caption(image: Image.Image) -> None:
    # A subtle shadow band gives the two exact caption lines clean contrast.
    shade = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    band = Image.new("L", (WIDTH, HEIGHT), 0)
    band_draw = ImageDraw.Draw(band)
    band_draw.rectangle((0, 245, WIDTH, 510), fill=52)
    band = band.filter(ImageFilter.GaussianBlur(72))
    shade.putalpha(band)
    image.alpha_composite(shade)

    font = ImageFont.truetype(str(FONT), 132)
    try:
        axes = font.get_variation_axes()
        if axes:
            font.set_variation_by_axes([min(620, axes[0]["maximum"])] + [axis["default"] for axis in axes[1:]])
    except (AttributeError, OSError, TypeError):
        pass
    subtitle_font = ImageFont.truetype(str(FONT), 30)

    text_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    tracked_text(draw, "Esia", WIDTH // 2, 275, font, (245, 248, 255, 255), 7)
    tracked_text(draw, "systems, robotics, engineering", WIDTH // 2, 430,
                 subtitle_font, (214, 226, 247, 245), 3)

    glow = text_layer.getchannel("A").filter(ImageFilter.GaussianBlur(15))
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (133, 175, 255, 0))
    glow_layer.putalpha(glow.point(lambda pixel: round(pixel * 0.24)))
    image.alpha_composite(glow_layer)
    image.alpha_composite(text_layer)


def main() -> None:
    rng = random.Random(SEED)
    image = Image.new("RGBA", (WIDTH, HEIGHT))
    pixels = image.load()
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        color = (3 + round(t * 2), 6 + round(t * 3), 18 + round(t * 7), 255)
        for x in range(WIDTH):
            pixels[x, y] = color

    add_nebula(image, cloud_noise(rng))
    draw_background_stars(image, rng)
    draw_feature_stars(image)
    add_caption(image)

    # Gentle edge falloff keeps the luminous center and its caption dominant.
    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    v = vignette.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            dx = (x - WIDTH / 2) / (WIDTH * 0.72)
            dy = (y - HEIGHT / 2) / (HEIGHT * 0.76)
            v[x, y] = max(0, min(90, round((dx * dx + dy * dy) * 40)))
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 8, 255))
    dark.putalpha(vignette)
    image.alpha_composite(dark)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(OUTPUT, format="PNG", optimize=True)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
