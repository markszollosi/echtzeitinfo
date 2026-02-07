# Echtzeitinfo

Real-time Vienna public transport departure display for a Raspberry Pi Zero W 2 with a Waveshare 7.5" V2 e-paper screen (800x480, B/W).

Sits next to the apartment door for a quick glance at upcoming departures before leaving.

## How it works

1. Fetches real-time departures from the [Wiener Linien API](https://www.data.gv.at/katalog/dataset/wiener-linien-echtzeitdaten-via-datendrehscheibe-wien)
2. Renders a clean departure board with station names, line numbers, directions, and next 3 departure countdowns
3. Updates the e-paper display every 60 seconds (configurable)
4. Periodic full refresh to prevent ghosting

## Display layout

```
┌─────────────────────────────────────┐
│ ● Rochusgasse                       │
│   U3  Ottakring           3'  7' 12'│
│   U3  Simmering           1'  5' 14'│
│─────────────────────────────────────│
│ ● Landstraße                        │
│   U3  Ottakring           2'  8' 15'│
│   U4  Heiligenstadt       1'  4'  9'│
│                                     │
│                  Aktualisiert 14:32 │
│ Datenquelle: Stadt Wien             │
└─────────────────────────────────────┘
```

## Setup

### Desktop testing (no hardware needed)

```bash
uv venv && uv pip install -r requirements.txt
```

Set `simulate: true` in `config.yaml`, then:

```bash
.venv/bin/python -m src.main
```

PNG files will be saved to `output/`.

### Raspberry Pi

```bash
git clone https://github.com/markszollosi/echtzeitinfo.git
cd echtzeitinfo
./setup_pi.sh
```

This enables SPI, installs dependencies (using `uv`), clones the Waveshare e-Paper library, and installs a systemd service.

Then edit `config.yaml` with your stations and start:

```bash
sudo systemctl start echtzeitinfo
journalctl -u echtzeitinfo -f
```

## Configuration

Edit `config.yaml`:

```yaml
stations:
  - name: "Rochusgasse"
    rbls: [4903, 4904]       # RBL numbers for this stop
  - name: "Landstraße"
    rbls: [146, 145]

refresh_interval: 60          # seconds between API calls
full_refresh_every: 5         # full e-paper refresh every N cycles

display:
  type: "epd7in5_V2"
  simulate: false             # true = output PNG instead of hardware
  output_dir: "output"
```

RBL numbers identify specific stops/platforms. You can find them via the [Wiener Linien CSV data](https://data.wien.gv.at/csv/wienerlinien-ogd-haltepunkte.csv).

## Hardware

- Raspberry Pi Zero W 2
- Waveshare 7.5" V2 e-paper display (800x480, B/W)
- Connect via **PH2.0 cable**, not the HAT connector (the Pi Zero has a known issue where the 5V HAT circuit causes reboots when RST is toggled)
- 5V 2.5A+ power supply recommended

## API

Uses the Wiener Linien real-time API (`/ogd_realtime/monitor`). No API key required. Minimum 15-second polling interval.

Test the API standalone:

```bash
.venv/bin/python -m src.api
```

Datenquelle: Stadt Wien — data.wien.gv.at
