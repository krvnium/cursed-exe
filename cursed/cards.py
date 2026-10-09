import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji


CARD_WIDTH = 1000
CARD_HEIGHT = 640
INK = "#111111"
CREAM = "#fff8ef"
PINK = "#ffb3c6"
LIME = "#c8ffb0"
LAVENDER = "#d9c2ff"


def draw_neobrutalist_box(
    draw: ImageDraw.Draw,
    xy: list,
    bg_color: str,
    outline_width: int = 4,
    shadow_offset: int = 6,
):
    shadow_xy = [
        xy[0] + shadow_offset,
        xy[1] + shadow_offset,
        xy[2] + shadow_offset,
        xy[3] + shadow_offset,
    ]
    draw.rectangle(shadow_xy, fill=INK)
    draw.rectangle(xy, fill=bg_color, outline=INK, width=outline_width)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "assets",
        "fonts",
        "BricolageGrotesque.ttf",
    )
    try:
        return ImageFont.truetype(font_path, size)
    except OSError:
        return ImageFont.load_default()


def _wrap_to_width(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)

    if not lines:
        return [""]
    if len(lines) <= max_lines:
        return lines
    clipped = lines[:max_lines]
    clipped[-1] = clipped[-1].rstrip(". ") + "..."
    return clipped


def _fit_lines(
    draw: ImageDraw.Draw,
    text: str,
    max_width: int,
    max_height: int,
    preferred_size: int,
    minimum_size: int = 12,
) -> tuple[ImageFont.ImageFont, list[str], int]:
    for size in range(preferred_size, minimum_size - 1, -1):
        font = _font(size)
        line_height = max(size + 5, 16)
        max_lines = max(1, max_height // line_height)
        lines = _wrap_to_width(draw, text, font, max_width, max_lines)
        if len(lines) * line_height <= max_height:
            return font, lines, line_height
    font = _font(minimum_size)
    line_height = minimum_size + 5
    return font, _wrap_to_width(
        draw, text, font, max_width, max(1, max_height // line_height)
    ), line_height


def _draw_text_block(
    pilmoji: Pilmoji,
    draw: ImageDraw.Draw,
    text: str,
    box: list[int],
    preferred_size: int,
    fill: str = INK,
    minimum_size: int = 12,
):
    padding = 14
    font, lines, line_height = _fit_lines(
        draw,
        text,
        box[2] - box[0] - padding * 2,
        box[3] - box[1] - padding * 2,
        preferred_size,
        minimum_size,
    )
    for index, line in enumerate(lines):
        pilmoji.text(
            (box[0] + padding, box[1] + padding + index * line_height),
            line,
            fill=fill,
            font=font,
        )


def render_card(
    pixel_image: Image.Image,
    metadata: dict,
    rarity: str = "Rare",
    stats: dict = None,
) -> Image.Image:
    """Render a fixed-size horizontal card with bounded, readable metadata."""
    stats = stats or {"Chaotic-ness": 99, "Grass Meter": 0}
    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), CREAM)
    draw = ImageDraw.Draw(card)

    draw.rectangle([0, 0, CARD_WIDTH - 1, CARD_HEIGHT - 1], outline=INK, width=8)

    image_box = [30, 30, 580, 580]
    draw_neobrutalist_box(draw, image_box, LIME)
    art_box = [50, 50, 560, 560]
    resized_art = pixel_image.resize((510, 510), Image.Resampling.NEAREST)
    card.paste(resized_art, (art_box[0], art_box[1]))
    draw.rectangle(art_box, outline=INK, width=4)

    right_x1, right_x2 = 610, 960
    name_box = [right_x1, 30, right_x2, 105]
    identity_box = [right_x1, 120, right_x2, 180]
    stats_box = [right_x1, 195, right_x2, 315]
    quote_box = [right_x1, 330, right_x2, 425]
    lore_box = [right_x1, 440, right_x2, 600]

    for box, color in (
        (name_box, PINK),
        (identity_box, LAVENDER),
        (stats_box, LIME),
        (quote_box, CREAM),
        (lore_box, PINK),
    ):
        draw_neobrutalist_box(draw, box, color)

    with Pilmoji(card) as pilmoji:
        _draw_text_block(
            pilmoji,
            draw,
            metadata.get("name", "UNKNOWN").upper(),
            name_box,
            preferred_size=34,
            minimum_size=18,
        )
        _draw_text_block(
            pilmoji,
            draw,
            f"CLASS  {metadata.get('class', 'GLITCH')}   •   {rarity.upper()}",
            identity_box,
            preferred_size=18,
            minimum_size=12,
        )
        _draw_text_block(pilmoji, draw, "STATS", [*stats_box[:2], stats_box[2], stats_box[1] + 42], 20)
        stat_lines = [
            f"Chaotic-ness  {max(0, min(100, int(stats.get('Chaotic-ness', 0)) ))}",
            f"Grass Meter  {max(0, min(100, int(stats.get('Grass Meter', 0)) ))}",
        ]
        for index, line in enumerate(stat_lines):
            _draw_text_block(
                pilmoji,
                draw,
                line,
                [stats_box[0], stats_box[1] + 40 + index * 34, stats_box[2], stats_box[1] + 75 + index * 34],
                preferred_size=17,
                minimum_size=12,
            )
        _draw_text_block(
            pilmoji,
            draw,
            f'"{metadata.get("quirky_text", "Error 404: Vibe not found.")}"',
            quote_box,
            preferred_size=16,
            minimum_size=12,
        )
        _draw_text_block(
            pilmoji,
            draw,
            metadata.get("lore", "Data corrupted."),
            lore_box,
            preferred_size=16,
            minimum_size=12,
        )

    return card
