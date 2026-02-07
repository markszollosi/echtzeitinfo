"""Echtzeitinfo — Vienna public transport departure display."""

import logging
import signal
import sys
import time
from pathlib import Path

import yaml

from src.api import fetch_departures, group_by_station
from src.display import Display
from src.renderer import render_departures

logger = logging.getLogger("echtzeitinfo")

_running = True


def _shutdown(signum, frame):
    global _running
    logger.info("Received signal %d, shutting down...", signum)
    _running = False


def load_config(path: str = "config.yaml") -> dict:
    config_path = Path(path)
    if not config_path.exists():
        logger.error("Config file not found: %s", path)
        sys.exit(1)
    with open(config_path) as f:
        return yaml.safe_load(f)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    config = load_config(config_path)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    # Collect all RBLs
    all_rbls = []
    for station in config["stations"]:
        all_rbls.extend(station["rbls"])

    refresh_interval = config.get("refresh_interval", 60)

    # Merge display config with full_refresh_every from top level
    display_config = config.get("display", {})
    display_config["full_refresh_every"] = config.get("full_refresh_every", 5)

    display = Display(display_config)

    try:
        display.init()

        while _running:
            # Fetch
            logger.info("Fetching departures for RBLs: %s", all_rbls)
            monitors = fetch_departures(all_rbls)
            stations_data = group_by_station(monitors, config["stations"])

            # Render
            image = render_departures(stations_data)

            # Update display
            display.update(image)

            # Sleep in small increments so we can respond to signals
            for _ in range(refresh_interval):
                if not _running:
                    break
                time.sleep(1)

    except Exception:
        logger.exception("Unexpected error")
    finally:
        logger.info("Cleaning up display...")
        display.clear()
        display.sleep()
        logger.info("Goodbye.")


if __name__ == "__main__":
    main()
