#!/bin/bash
# ADS-B Telegram Bot Installer
# Version: 1.5

echo "🚀 ADS-B Telegram Bot Installer"
echo "=============================="

# Install location
INSTALL_DIR="/home/pi"
BOT_FILE="${INSTALL_DIR}/bot_adsb.py"
CONFIG_FILE="${INSTALL_DIR}/config.py"

# Install dependency
echo "🐍 Installing python-telegram-bot..."
sudo python3 -m pip install python-telegram-bot --upgrade --break-system-packages

# Download files
echo "📥 Downloading files..."
sudo curl -sL -o "${BOT_FILE}" https://raw.githubusercontent.com/bersuc/adsb-telegram-bot/main/bot.py
sudo curl -sL -o "${CONFIG_FILE}" https://raw.githubusercontent.com/bersuc/adsb-telegram-bot/main/config.py

# Set permissions
sudo chown pi:pi "${BOT_FILE}" "${CONFIG_FILE}"
sudo chmod +x "${BOT_FILE}"

# Create systemd service running as user 'pi'
echo "⚙️ Creating systemd service (running as user pi)..."
sudo tee /etc/systemd/system/adsb-telegram-bot.service > /dev/null << 'EOF'
[Unit]
Description=Bot do Telegram para Monitoramento ADSB
After=network.target dump1090-fa.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/bot_adsb.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now adsb-telegram-bot.service

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "Next steps:"
echo "   1. Edit the configuration file:"
echo "      nano /home/pi/config.py"
echo ""
echo "Service commands:"
echo "   sudo systemctl status adsb-telegram-bot.service"
echo "   sudo journalctl -u adsb-telegram-bot.service -f"
echo "   sudo systemctl restart adsb-telegram-bot.service"
echo ""
echo "To update the bot later, run the update script."