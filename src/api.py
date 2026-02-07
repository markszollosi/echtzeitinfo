"""Wiener Linien real-time departure API client."""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

API_URL = "https://www.wienerlinien.at/ogd_realtime/monitor"
REQUEST_TIMEOUT = 10

# API error codes
ERROR_CODES = {
    311: "no departures found",
    316: "invalid RBL number",
    320: "service unavailable",
}


def fetch_departures(rbls: list[int]) -> list[dict[str, Any]]:
    """Fetch real-time departures for the given RBL numbers.

    Returns a list of monitor dicts, each containing:
        - rbl: int
        - lines: list of dicts with keys:
            - name: str (e.g. "U3")
            - towards: str (e.g. "Ottakring")
            - departures: list of dicts with keys:
                - countdown: int (minutes)
                - realtime: bool
    """
    params = [("rbl", rbl) for rbl in rbls]

    try:
        resp = requests.get(API_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("API request failed: %s", e)
        return []

    data = resp.json()

    message = data.get("message", {})
    server_code = message.get("serverCode")
    if server_code and server_code != 200:
        desc = ERROR_CODES.get(server_code, message.get("value", "unknown error"))
        logger.warning("API returned code %d: %s", server_code, desc)

    monitors = []
    for monitor in data.get("data", {}).get("monitors", []):
        rbl = monitor.get("locationStop", {}).get("properties", {}).get("attributes", {}).get("rbl")

        for line_data in monitor.get("lines", []):
            line_name = line_data.get("name", "?").strip()
            towards = line_data.get("towards", "?").strip().title()

            departures = []
            for dep in line_data.get("departures", {}).get("departure", []):
                dep_time = dep.get("departureTime", {})
                countdown = dep_time.get("countdown")
                if countdown is not None:
                    departures.append({
                        "countdown": countdown,
                        "realtime": dep_time.get("timePlanned") != dep_time.get("timeReal"),
                    })

            monitors.append({
                "rbl": rbl,
                "name": line_name,
                "towards": towards,
                "departures": departures,
            })

    return monitors


def group_by_station(monitors: list[dict], stations_config: list[dict]) -> list[dict]:
    """Group monitor data by configured stations.

    Returns a list of dicts:
        - name: station name
        - lines: list of line dicts (name, towards, departures)
    """
    result = []
    for station in stations_config:
        station_rbls = set(station["rbls"])
        lines = [m for m in monitors if m.get("rbl") in station_rbls]

        # Deduplicate lines with same name+direction (case-insensitive),
        # merge departures and keep earliest countdowns
        seen = {}
        for line in lines:
            key = (line["name"].upper(), line["towards"].upper())
            if key not in seen:
                seen[key] = line
            else:
                existing = seen[key]
                merged = existing["departures"] + line["departures"]
                merged.sort(key=lambda d: d["countdown"])
                existing["departures"] = merged

        result.append({
            "name": station["name"],
            "lines": sorted(seen.values(), key=lambda l: (l["name"], l["towards"])),
        })

    return result


if __name__ == "__main__":
    import json
    import sys

    import yaml

    logging.basicConfig(level=logging.DEBUG)

    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    all_rbls = []
    for station in config["stations"]:
        all_rbls.extend(station["rbls"])

    raw = fetch_departures(all_rbls)
    grouped = group_by_station(raw, config["stations"])
    print(json.dumps(grouped, indent=2, ensure_ascii=False))
