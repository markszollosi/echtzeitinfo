"""PIL-based layout engine for the departure display."""

import logging
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

WIDTH = 800
HEIGHT = 480

# Font paths — try system DejaVu first, fall back to bundled fonts dir
_FONT_DIRS = [
    Path("/usr/share/fonts/truetype/dejavu"),
    Path(__file__).resolve().parent.parent / "fonts",
]


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    for font_dir in _FONT_DIRS:
        path = font_dir / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    logger.warning("Font %s not found, using default", name)
    return ImageFont.load_default()


# Fonts
FONT_STATION = None
FONT_LINE = None
FONT_DIRECTION = None
FONT_COUNTDOWN = None
FONT_TIMESTAMP = None
FONT_ATTRIBUTION = None


def _init_fonts():
    global FONT_STATION, FONT_LINE, FONT_DIRECTION, FONT_COUNTDOWN
    global FONT_TIMESTAMP, FONT_ATTRIBUTION
    FONT_STATION = _load_font("DejaVuSans-Bold.ttf", 28)
    FONT_LINE = _load_font("DejaVuSans-Bold.ttf", 24)
    FONT_DIRECTION = _load_font("DejaVuSans.ttf", 22)
    FONT_COUNTDOWN = _load_font("DejaVuSans-Bold.ttf", 24)
    FONT_TIMESTAMP = _load_font("DejaVuSans.ttf", 16)
    FONT_ATTRIBUTION = _load_font("DejaVuSans.ttf", 12)


# Layout constants
MARGIN_X = 20
MARGIN_Y = 15
STATION_HEIGHT = 36
LINE_HEIGHT = 34
SEPARATOR_GAP = 12
COUNTDOWN_COLS = 3
COUNTDOWN_WIDTH = 50


def render_departures(stations_data: list[dict], width: int = WIDTH, height: int = HEIGHT) -> Image.Image:
    """Render departure data to a 1-bit PIL Image.

    Args:
        stations_data: output of api.group_by_station()
        width: image width in pixels
        height: image height in pixels

    Returns:
        PIL Image in mode "1" (1-bit black and white)
    """
    if FONT_STATION is None:
        _init_fonts()

    img = Image.new("1", (width, height), 1)  # 1 = white
    draw = ImageDraw.Draw(img)

    y = MARGIN_Y

    for i, station in enumerate(stations_data):
        # Station separator line (not before first station)
        if i > 0:
            y += SEPARATOR_GAP // 2
            draw.line([(MARGIN_X, y), (width - MARGIN_X, y)], fill=0, width=1)
            y += SEPARATOR_GAP // 2

        # Station name header
        draw.text((MARGIN_X, y), f"\u25cf {station['name']}", font=FONT_STATION, fill=0)
        y += STATION_HEIGHT

        # Lines
        for line in station.get("lines", []):
            _draw_line_row(draw, y, line, width)
            y += LINE_HEIGHT

    # Timestamp at bottom right
    now = datetime.now().strftime("Aktualisiert %H:%M:%S")
    ts_bbox = draw.textbbox((0, 0), now, font=FONT_TIMESTAMP)
    ts_width = ts_bbox[2] - ts_bbox[0]
    draw.text((width - MARGIN_X - ts_width, height - 40), now, font=FONT_TIMESTAMP, fill=0)

    # Attribution at bottom left
    attribution = "Datenquelle: Stadt Wien \u2014 data.wien.gv.at"
    draw.text((MARGIN_X, height - 22), attribution, font=FONT_ATTRIBUTION, fill=0)

    return img


def _draw_line_row(draw: ImageDraw.ImageDraw, y: int, line: dict, width: int):
    """Draw a single departure line row."""
    x = MARGIN_X + 16  # indent under station name

    # Line name (e.g. "U3")
    draw.text((x, y), line["name"], font=FONT_LINE, fill=0)
    line_bbox = draw.textbbox((x, y), line["name"], font=FONT_LINE)
    x_after_line = line_bbox[2] + 12

    # Direction (e.g. "Ottakring")
    max_dir_width = width - MARGIN_X - (COUNTDOWN_COLS * COUNTDOWN_WIDTH) - x_after_line - 10
    direction = line["towards"]
    # Truncate direction if too long
    dir_bbox = draw.textbbox((0, 0), direction, font=FONT_DIRECTION)
    if dir_bbox[2] - dir_bbox[0] > max_dir_width:
        while len(direction) > 3:
            direction = direction[:-1]
            bbox = draw.textbbox((0, 0), direction + "\u2026", font=FONT_DIRECTION)
            if bbox[2] - bbox[0] <= max_dir_width:
                direction += "\u2026"
                break

    draw.text((x_after_line, y + 2), direction, font=FONT_DIRECTION, fill=0)

    # Countdown columns (right-aligned)
    departures = line.get("departures", [])[:COUNTDOWN_COLS]
    countdown_start_x = width - MARGIN_X - COUNTDOWN_COLS * COUNTDOWN_WIDTH

    for j, dep in enumerate(departures):
        minutes = dep["countdown"]
        text = str(minutes) + "'"
        col_x = countdown_start_x + j * COUNTDOWN_WIDTH
        # Right-align within column
        bbox = draw.textbbox((0, 0), text, font=FONT_COUNTDOWN)
        text_w = bbox[2] - bbox[0]
        draw.text((col_x + COUNTDOWN_WIDTH - text_w, y), text, font=FONT_COUNTDOWN, fill=0)
