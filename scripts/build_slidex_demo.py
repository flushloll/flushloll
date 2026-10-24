"""Render a short SlideX deck sequence using the repository's public UI palette."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "projects" / "slidex-live-demo.gif"
WIDTH, HEIGHT = 720, 470
FONT_DIR = Path("/usr/share/fonts/truetype/liberation")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / name
    if not path.exists():
        return ImageFont.load_default()
    return ImageFont.truetype(str(path), size)


def centered_text(draw: ImageDraw.ImageDraw, text: str, y: int,
                  face: ImageFont.FreeTypeFont, fill: str) -> None:
    draw.text((WIDTH / 2, y), text, font=face, fill=fill, anchor="mt")


def slide(title: str, bullets: tuple[str, ...], number: int, title_slide: bool = False) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f1f3f4")
    draw = ImageDraw.Draw(image)
    # SlideX public/deck.html header and status bar.
    draw.rectangle((0, 0, WIDTH, 46), fill="#ffffff")
    draw.line((0, 45, WIDTH, 45), fill="#dadce0", width=1)
    draw.text((22, 16), "SLIDEX", font=font("LiberationSans-Bold.ttf", 13), fill="#5f6368")
    draw.text((WIDTH - 22, 17), "●  LIVE / LISTENING", font=font("LiberationMono-Bold.ttf", 11),
              fill="#188038", anchor="rt")

    # The source page presents one 16:9 slide in a centered white frame.
    left, top, right, bottom = 40, 56, 680, 416
    draw.rectangle((left + 3, top + 5, right + 3, bottom + 5), fill="#d8dadd")
    draw.rectangle((left, top, right, bottom), fill="#ffffff")

    if title_slide:
        draw.rectangle((left, top, right, bottom), fill="#fbfcfe")
        title_font = font("LiberationSans-Bold.ttf", 49)
        centered_text(draw, title, 154, title_font, "#202124")
        centered_text(draw, "LIVE PRESENTATION", 239, font("LiberationSans-Bold.ttf", 12), "#4285f4")
    else:
        draw.text((86, 112), title, font=font("LiberationSans-Bold.ttf", 35), fill="#202124")
        y = 190
        for bullet in bullets:
            draw.ellipse((91, y + 7, 101, y + 17), fill="#4285f4")
            draw.text((116, y), bullet, font=font("LiberationSans-Regular.ttf", 20), fill="#3c4043")
            y += 43
        draw.text((652, 389), f"{number:02d}", font=font("LiberationMono-Bold.ttf", 11),
                  fill="#5f6368", anchor="rt")

    # The real viewer's compact transport controls sit below the slide frame.
    draw.rounded_rectangle((294, 432, 426, 464), radius=16, fill="#ffffff", outline="#dadce0")
    draw.text((319, 437), "‹", font=font("LiberationSans-Regular.ttf", 18), fill="#5f6368", anchor="mt")
    draw.text((360, 443), f"{number} / 4", font=font("LiberationMono-Bold.ttf", 8),
              fill="#5f6368", anchor="mt")
    draw.text((400, 437), "›", font=font("LiberationSans-Regular.ttf", 18), fill="#5f6368", anchor="mt")
    return image


def main() -> None:
    slides = [
        slide("Slides from speech", (), 1, title_slide=True),
        slide("Talk, then watch the deck change", (
            "Microphone audio streams to Realtime.",
            "Tool calls create and revise slides.",
            "The browser follows the active slide.",
        ), 2),
        slide("Keep the audience in sync", (
            "Updates appear as they are made.",
            "Finished slides stay in place.",
            "The current slide is easy to follow.",
        ), 3),
        slide("Share the live display", (
            "Open the browser deck for viewers.",
            "Publish updates through the API.",
            "Slides can include sourced images.",
        ), 4),
    ]

    # Hold each slide briefly, then use SlideX's horizontal fade/slide transition.
    frames: list[Image.Image] = []
    for index, current in enumerate(slides):
        frames.extend([current] * 4)
        if index + 1 < len(slides):
            following = slides[index + 1]
            # Match the browser viewer: the active 16:9 slide moves out as the
            # new slide enters, while the surrounding deck UI stays fixed.
            left, top, right, bottom = 40, 56, 680, 416
            current_panel = current.crop((left, top, right, bottom))
            next_panel = following.crop((left, top, right, bottom))
            for step in range(1, 5):
                progress = step / 5
                moved = current.copy()
                draw = ImageDraw.Draw(moved)
                draw.rectangle((left, top, right, bottom), fill="#ffffff")
                moved.paste(current_panel, (left - round(progress * (right - left)), top))
                moved.paste(next_panel, (left + round((1 - progress) * (right - left)), top))
                frames.append(moved)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:], duration=250,
                   loop=0, optimize=True, disposal=2)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes, {len(frames)} frames)")


if __name__ == "__main__":
    main()
