#!/bin/bash
# ADS-B Telegram Bot Installer
# Version: 1.6 - Ajustada e mais robusta

echo "🚀 ADS-B Telegram Bot Installer"
echo "=============================="

# Instalar pip se necessário
echo "🐍 Verificando python3-pip..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip

# Instalar pacote
echo "📦 Instalando python-telegram-bot..."
sudo python3 -m pip install python-telegram-bot --upgrade --break-system-packages

# Create directory
sudo mkdir -p /opt/adsb-telegram-bot
cd /opt/adsb-telegram-bot

# Set correct permissions
sudo chown -R pi:pi /opt/adsb-telegram-bot

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

# Create systemd service (running as user pi)
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/adsb-telegram-bot.service > /dev/null << 'EOF'
[Unit]
Description=ADSB Telegram Bot Monitoring Service
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
echo "      nano /opt/adsb-telegram-bot/config.py"
echo ""
echo "Service commands:"
echo "   sudo systemctl status adsb-telegram-bot.service"
echo "   sudo journalctl -u adsb-telegram-bot.service -f"
echo "   sudo systemctl restart adsb-telegram-bot.service"
echo ""
echo "To update the bot later, just run this installer again."