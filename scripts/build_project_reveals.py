"""Build one-shot project tile reveals. Requires Pillow and CairoSVG."""
from __future__ import annotations

import io
import re
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1] / "assets" / "projects"
OUTPUT = ROOT / "reveal"
TOOL_ICONS = ROOT.parent / "tools"
MAX_SIZE = (320, 420)
FADE_STEPS = 12
GAP_MS = 120
CARD_AFTER_REVEAL_MS = 9000
CARD_FADE_STEPS = 12

# Ordered by rating, then by a red-to-violet progression around the color wheel.
# Fade duration and the gap after each fade both shrink, like a bouncing ball.
ITEMS = [
    ("mist", "mist-project.gif", 1300, "#F47B72", ("creo", "raspberrypi", "go"), 2),
    ("matetra", "names/matetra.svg", 1200, "#F39F65", ("go", "godotengine"), 1),
    ("cluck-n-cook", "cluck-n-cook.gif", 1100, "#F39F65", ("godotengine",), 2),
    ("groups", "groups-neon-city.png", 1000, "#D5D968", ("react", "threedotjs", "typescript"), 1),
    ("soup-hopper", "soup-hopper.gif", 900, "#A5D77A", ("arduino", "espressif", "python"), 2),
    ("fallout-business-badge", "fallout-business-badge-first.png", 800, "#7BD29B", ("kicad", "espressif", "adafruit"), 1),
    ("slidex", "slidex.svg", 700, "#67C8B5", ("python", "openai"), 1),
    ("computer-vision", "computer-vision-reel-v3.gif", 600, "#6DBDDB", ("python", "opencv"), 1),
    ("daydream-2025", "daydream-2025.svg", 500, "#A38CE8", ("godotengine",), 1),
]


def split_time(total_ms: int, count: int) -> list[int]:
    quotient, remainder = divmod(total_ms, count)
    return [quotient + (i < remainder) for i in range(count)]


def load_frames(source: Path, name: str) -> tuple[list[Image.Image], list[int]]:
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
        speed = 200
    elif name == "soup-hopper":
        speed = 200
    elif name == "cluck-n-cook":
        speed = 125
    elif name == "computer-vision":
        speed = 180
    else:
        speed = 350
    durations = [speed] * len(frames)
    return frames, durations


def tool_mark(name: str, max_size: int) -> Image.Image:
    source = TOOL_ICONS / f"{name}.svg"
    svg = source.read_bytes()
    svg = re.sub(rb'fill="currentColor"', b'fill="#151C26"', svg)
    root = re.search(rb'<svg\b[^>]*>', svg).group(0)
    if re.search(rb'\bfill="', root):
        recolored_root = re.sub(rb'\bfill="[^"]*"', b'fill="#151C26"', root, count=1)
    else:
        recolored_root = root[:-1] + b' fill="#151C26">'
    svg = svg.replace(root, recolored_root, 1)
    match = re.search(rb'viewBox="([\d. -]+)"', svg)
    _, _, view_width, view_height = map(float, match.group(1).split())
    ratio = view_width / view_height
    out_width = max(1, round(max_size * min(ratio, 1)))
    out_height = max(1, round(max_size * min(1 / ratio, 1)))
    raster = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg, output_width=out_width, output_height=out_height))).convert("RGBA")
    alpha = raster.getchannel("A")
    mark = Image.new("RGBA", raster.size, (21, 28, 38, 0))
    mark.putalpha(alpha)
    return mark


def skill_card(size: tuple[int, int], color: str, tools: tuple[str, ...]) -> Image.Image:
    width, height = size
    image = Image.new("RGBA", size, color)
    draw = ImageDraw.Draw(image)
    count = len(tools)
    gap = max(8, width // 30)
    badge = min(88, (width - 24 - gap * (count - 1)) // count, max(54, height // 2))
    total = count * badge + (count - 1) * gap
    x = (width - total) // 2
    y = (height - badge) // 2
    for tool in tools:
        draw.rounded_rectangle((x, y, x + badge, y + badge), radius=badge // 2, fill=(249, 250, 248, 238))
        icon = tool_mark(tool, round(badge * 0.66))
        image.alpha_composite(icon, (x + (badge - icon.width) // 2, y + (badge - icon.height) // 2))
        x += badge + gap
    return image


def make_reveal(name: str, source: str, start_ms: int, fade_ms: int, color: str, tools: tuple[str, ...], max_loops: int) -> None:
    sources, source_durations = load_frames(ROOT / source, name)
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

    # Card transitions share one offset, preserving the reveal order and spacing.
    # Short clips repeat at most twice; any remaining time holds the last clip frame.
    content_ms = max(0, CARD_AFTER_REVEAL_MS - fade_ms)
    if len(sources) > 1:
        remaining = content_ms
        cycle = list(zip(sources[1:] + sources[:1], source_durations[1:] + source_durations[:1]))
        for _ in range(max_loops):
            for source_frame, source_ms in cycle:
                if not remaining:
                    break
                frame_ms = min(source_ms, remaining)
                frames.append(source_frame.copy())
                durations.append(frame_ms)
                remaining -= frame_ms
        if remaining:
            frames.append(frames[-1].copy())
            durations.append(remaining)
    else:
        frames.append(base.copy())
        durations.append(content_ms)

    card = skill_card(base.size, color, tools).convert("RGB")
    last = frames[-1].convert("RGB")
    for alpha, frame_ms in zip(range(1, CARD_FADE_STEPS + 1), split_time(fade_ms, CARD_FADE_STEPS)):
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
    for index, (name, source, fade, color, tools, max_loops) in enumerate(ITEMS):
        make_reveal(name, source, start, fade, color, tools, max_loops)
        # Each interval contracts as the reveals accelerate.
        start += fade + max(45, GAP_MS - index * 9)


if __name__ == "__main__":
    main()
