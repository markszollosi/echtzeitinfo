"""E-paper display abstraction with hardware and simulate modes."""

import logging
from datetime import datetime
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


class Display:
    """Wraps e-paper hardware or simulates output to PNG files."""

    def __init__(self, config: dict):
        self._simulate = config.get("simulate", False)
        self._output_dir = Path(config.get("output_dir", "output"))
        self._epd_type = config.get("type", "epd7in5_V2")
        self._full_refresh_every = config.get("full_refresh_every", 5)
        self._cycle_count = 0
        self._epd = None

    def init(self):
        """Initialize the display."""
        if self._simulate:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Simulate mode: output to %s/", self._output_dir)
        else:
            self._epd = self._load_epd()
            self._epd.init()
            self._epd.Clear()
            logger.info("E-paper display initialized (full clear)")

    def _load_epd(self):
        """Dynamically load the Waveshare EPD module."""
        try:
            from waveshare_epd import epd7in5_V2
            return epd7in5_V2.EPD()
        except ImportError:
            logger.error(
                "waveshare_epd not found. Install the Waveshare e-Paper library: "
                "https://github.com/waveshare/e-Paper"
            )
            raise

    def update(self, image: Image.Image):
        """Send an image to the display (or save as PNG in simulate mode)."""
        self._cycle_count += 1
        needs_full_refresh = (self._cycle_count % self._full_refresh_every) == 0

        if self._simulate:
            filename = datetime.now().strftime("departure_%Y%m%d_%H%M%S.png")
            path = self._output_dir / filename
            image.save(str(path))
            refresh_type = "full" if needs_full_refresh else "partial"
            logger.info("Saved %s (cycle %d, %s refresh)", path, self._cycle_count, refresh_type)
        else:
            if needs_full_refresh:
                logger.info("Full refresh (cycle %d)", self._cycle_count)
                self._epd.init()
                self._epd.Clear()
                self._epd.init()
            else:
                logger.debug("Fast refresh (cycle %d)", self._cycle_count)
                try:
                    self._epd.init_fast()
                except AttributeError:
                    # Older library versions may not have init_fast
                    self._epd.init()

            self._epd.display(self._epd.getbuffer(image))

    def clear(self):
        """Clear the display to white."""
        if self._simulate:
            logger.info("Simulate: clear display")
        else:
            if self._epd:
                self._epd.init()
                self._epd.Clear()

    def sleep(self):
        """Put the display into low-power sleep mode."""
        if self._simulate:
            logger.info("Simulate: display sleep")
        else:
            if self._epd:
                self._epd.sleep()
                logger.info("Display entering sleep mode")
