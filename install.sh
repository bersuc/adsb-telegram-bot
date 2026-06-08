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

# Set permissions
sudo chown -R pi:pi /opt/adsb-telegram-bot

# Download files
echo "📥 Downloading files..."
sudo curl -sL -o bot.py https://raw.githubusercontent.com/bersuc/adsb-telegram-bot/main/bot.py
sudo curl -sL -o config.py https://raw.githubusercontent.com/bersuc/adsb-telegram-bot/main/config.py

# Set permissions
sudo chown pi:pi bot.py config.py
sudo chmod +x bot.py

# Create symlink
sudo ln -sf /opt/adsb-telegram-bot/bot.py /usr/local/bin/adsb-bot

# Create systemd service (running as user pi)
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/adsb-telegram-bot.service > /dev/null << 'EOF'
[Unit]
Description=ADS-B Telegram Bot for PiAware + dump1090-fa
After=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/opt/adsb-telegram-bot
ExecStart=/usr/bin/python3 /opt/adsb-telegram-bot/bot.py
Restart=always
RestartSec=5
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
echo "   1. Edit the configuration:"
echo "      nano /opt/adsb-telegram-bot/config.py"
echo ""
echo "Service commands:"
echo "   sudo systemctl status adsb-telegram-bot.service"
echo "   sudo journalctl -u adsb-telegram-bot.service -f"
echo "   sudo systemctl restart adsb-telegram-bot.service"
echo ""
echo "To update: run this installer again."