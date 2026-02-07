#!/usr/bin/env bash
# Setup script for Echtzeitinfo on Raspberry Pi Zero W 2
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WAVESHARE_DIR="$HOME/e-Paper"

echo "=== Echtzeitinfo Pi Setup ==="

# Enable SPI if not already enabled
if ! grep -q "^dtparam=spi=on" /boot/config.txt 2>/dev/null && \
   ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt 2>/dev/null; then
    echo "Enabling SPI..."
    sudo raspi-config nonint do_spi 0
    echo "SPI enabled. A reboot may be required."
else
    echo "SPI already enabled."
fi

# Install system packages
echo "Installing system packages..."
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-gpiozero \
    python3-spidev \
    python3-rpi.gpio \
    fonts-dejavu-core \
    git

# Install uv if not present
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create venv and install Python dependencies
echo "Setting up Python venv..."
cd "$SCRIPT_DIR"
uv venv
uv pip install -r requirements.txt

# Clone/update Waveshare e-Paper library
if [ -d "$WAVESHARE_DIR" ]; then
    echo "Updating Waveshare library..."
    cd "$WAVESHARE_DIR" && git pull
else
    echo "Cloning Waveshare e-Paper library..."
    git clone https://github.com/waveshare/e-Paper.git "$WAVESHARE_DIR"
fi

# Add Waveshare lib to venv via .pth file
SITE_PACKAGES=$("$SCRIPT_DIR/.venv/bin/python" -c "import site; print(site.getsitepackages()[0])")
echo "$WAVESHARE_DIR/RaspberryPi_JetsonNano/python/lib" > "$SITE_PACKAGES/waveshare-epd.pth"
echo "Waveshare library linked via $SITE_PACKAGES/waveshare-epd.pth"

# Install systemd service
echo "Installing systemd service..."
sudo cp "$SCRIPT_DIR/echtzeitinfo.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable echtzeitinfo.service
echo "Service installed and enabled."

echo ""
echo "=== Setup complete ==="
echo "Edit config.yaml to configure your stations, then:"
echo "  sudo systemctl start echtzeitinfo"
echo "  journalctl -u echtzeitinfo -f"
