"""Build one-shot project tile reveals. Requires Pillow and CairoSVG."""
from __future__ import annotations

import io
import math
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageOps, ImageSequence

ROOT = Path(__file__).resolve().parents[1] / "assets" / "projects"
OUTPUT = ROOT / "reveal"
MAX_SIZE = (320, 420)
FADE_STEPS = 12
GAP_MS = 120

# Reveal times shorten in sequence, like the intervals between ball bounces.
ITEMS = [
    ("groups", "groups-neon-city.png", 1300, 0, 7500, "#82E8D7", "web"),
    ("mist", "mist-project.gif", 1220, 3, 0, "#F4A37B", "cad"),
    ("soup-hopper", "soup-hopper.gif", 1140, 3, 0, "#76C8F5", "cad"),
    ("cluck-n-cook", "cluck-n-cook.gif", 1060, 3, 0, "#F6B65F", "game"),
    ("fallout-business-badge", "fallout-business-badge-first.png", 980, 0, 7500, "#B4DE76", "pcb"),
    ("daydream-2025", "daydream-2025.svg", 900, 0, 7500, "#B69BFF", "game"),
    ("computer-vision", "computer-vision-reel-v3.gif", 820, 2, 0, "#6CCFE0", "vision"),
    ("slidex", "slidex.svg", 740, 0, 7500, "#8BBDFF", "audio"),
]


def split_time(total_ms: int, count: int) -> list[int]:
    quotient, remainder = divmod(total_ms, count)
    return [quotient + (i < remainder) for i in range(count)]


def load_frames(source: Path, loop_count: int, name: str) -> tuple[list[Image.Image], list[int]]:
    if source.suffix.lower() == ".svg":
        data = cairosvg.svg2png(url=str(source), output_width=320)
        frame = Image.open(io.BytesIO(data)).convert("RGBA")
        return [ImageOps.contain(frame, MAX_SIZE, Image.Resampling.LANCZOS)], []

    im = Image.open(source)
    if im.n_frames == 1:
        frame = ImageOps.contain(im.convert("RGBA"), MAX_SIZE, Image.Resampling.LANCZOS)
        return [frame], []

    count = {"mist": 16, "soup-hopper": 18, "cluck-n-cook": 24}.get(name, 0)
    n = im.n_frames
    indices = list(range(n)) if not count else sorted({round(i * (n - 1) / (count - 1)) for i in range(count)})
    frames: list[Image.Image] = []
    for idx in indices:
        im.seek(idx)
        frame = ImageOps.contain(im.convert("RGBA").copy(), MAX_SIZE, Image.Resampling.LANCZOS)
        frames.append(frame)
    size = frames[0].size
    frames = [ImageOps.pad(frame, size, method=Image.Resampling.LANCZOS, color=(0, 0, 0, 0)) for frame in frames]

    if name == "mist":
        speed = 80
    elif name == "soup-hopper":
        speed = 100
    elif name == "cluck-n-cook":
        speed = 75
    else:
        speed = 350
    durations = [speed] * len(frames)
    return frames, durations


def skill_card(size: tuple[int, int], color: str, skill: str) -> Image.Image:
    width, height = size
    factor = 3
    W, H = width * factor, height * factor
    scale = min(W, H) * 0.72
    cx, cy = W / 2, H / 2
    ink = (21, 28, 38)
    image = Image.new("RGB", (W, H), color)
    draw = ImageDraw.Draw(image)
    stroke = max(5, int(scale * 0.045))

    def xy(x: float, y: float) -> tuple[int, int]:
        return int(cx + x * scale), int(cy + y * scale)

    def line(points: list[tuple[float, float]], width: int = stroke) -> None:
        draw.line([xy(x, y) for x, y in points], fill=ink, width=int(width), joint="curve")

    def box(bounds: tuple[float, float, float, float], radius: float = 0, width: int = stroke) -> None:
        x0, y0, x1, y1 = bounds
        bounds_px = (int(cx + x0 * scale), int(cy + y0 * scale), int(cx + x1 * scale), int(cy + y1 * scale))
        if radius:
            draw.rounded_rectangle(bounds_px, radius=int(radius * scale), outline=ink, width=int(width))
        else:
            draw.rectangle(bounds_px, outline=ink, width=int(width))

    def dot(x: float, y: float, r: float = 0.035) -> None:
        a, b = xy(x - r, y - r)
        c, d = xy(x + r, y + r)
        draw.ellipse((a, b, c, d), fill=ink)

    if skill == "cad":
        top, left, right, mid = (0, -.32), (-.29, -.15), (.29, -.15), (0, .02)
        low_left, low_right, bottom = (-.29, .19), (.29, .19), (0, .36)
        line([top, left, mid, right, top])
        line([left, low_left, bottom, low_right, right])
        line([mid, bottom])
    elif skill == "game":
        box((-.42, -.22, .42, .22), radius=.12)
        line([(-.25, -.12), (-.25, .12)])
        line([(-.37, 0), (-.13, 0)])
        dot(.17, -.08, .045)
        dot(.31, .08, .045)
    elif skill == "pcb":
        box((-.43, -.30, .43, .30), radius=.06)
        box((-.15, -.13, .15, .13), radius=.025, width=int(stroke * .9))
        for sx in (-1, 1):
            for sy in (-1, 1):
                line([(sx * .15, sy * .08), (sx * .28, sy * .08), (sx * .28, sy * .20), (sx * .35, sy * .20)])
                dot(sx * .37, sy * .20, .035)
        line([(-.15, 0), (-.32, 0), (-.32, -.20), (-.38, -.20)])
        dot(-.41, -.20, .035)
    elif skill == "vision":
        box((-.38, -.22, .38, .22), radius=.22)
        dot(0, 0, .16)
        dot(0, 0, .055)
        for x, y in ((-.46, -.30), (.46, -.30), (-.46, .30), (.46, .30)):
            dot(x, y, .028)
    elif skill == "web":
        box((-.43, -.30, .43, .30), radius=.05)
        line([(-.43, -.17), (.43, -.17)])
        for x in (-.32, -.23, -.14):
            dot(x, -.24, .018)
        box((-.32, -.08, -.08, .20), radius=.02, width=int(stroke * .75))
        box((.02, -.08, .32, .01), radius=.02, width=int(stroke * .75))
        box((.02, .08, .32, .20), radius=.02, width=int(stroke * .75))
    elif skill == "audio":
        box((-.34, -.30, .34, .06), radius=.04)
        line([(-.22, -.20), (-.05, -.20), (.07, -.08), (.20, -.20)])
        heights = (.10, .21, .32, .18, .27, .12, .23, .09)
        xs = (-.38, -.27, -.16, -.05, .06, .17, .28, .39)
        for x, h in zip(xs, heights):
            line([(x, .20 - h / 2), (x, .20 + h / 2)])
    return image.resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def make_reveal(name: str, source: str, start_ms: int, fade_ms: int, loops: int, hold_ms: int, color: str, skill: str) -> None:
    sources, source_durations = load_frames(ROOT / source, loops, name)
    base = sources[0]
    frames: list[Image.Image] = []
    durations: list[int] = []
    if start_ms:
        frames.append(Image.new("RGBA", base.size, (0, 0, 0, 0)))
        durations.append(start_ms)
    for alpha, frame_ms in zip(range(1, FADE_STEPS + 1), split_time(fade_ms, FADE_STEPS)):
        frame = base.copy()
        frame.putalpha(base.getchannel("A").point(lambda pixel, a=alpha: round(pixel * a / FADE_STEPS)))
        frames.append(frame)
        durations.append(frame_ms)

    if len(sources) > 1:
        # Repeat the clip as a unit; frame zero is already visible at fade completion.
        loop_frames = sources * loops
        loop_times = source_durations * loops
        frames.extend(loop_frames[1:])
        durations.extend(loop_times[1:])
    else:
        frames.append(base.copy())
        durations.append(hold_ms)

    card = skill_card(base.size, color, skill).convert("RGB")
    last = frames[-1].convert("RGB")
    for alpha, frame_ms in zip(range(1, FADE_STEPS + 1), split_time(1000, FADE_STEPS)):
        frames.append(Image.blend(last, card, alpha / FADE_STEPS).convert("RGBA"))
        durations.append(frame_ms)
    frames.append(card.convert("RGBA"))
    durations.append(12000)

    output = OUTPUT / f"{name}.webp"
    frames[0].save(output, format="WEBP", save_all=True, append_images=frames[1:], duration=durations, loop=1, quality=82, method=4, lossless=False)
    print(f"{name}: {len(frames)} frames, {sum(durations)/1000:.1f}s, {output.stat().st_size:,} bytes")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    start = 0
    for name, source, fade, loops, hold, color, skill in ITEMS:
        make_reveal(name, source, start, fade, loops, hold, color, skill)
        start += fade + GAP_MS


if __name__ == "__main__":
    main()
