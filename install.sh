#!/bin/bash
# ADS-B Telegram Bot Installer
# Version: 1.0

echo "🚀 ADS-B Telegram Bot Installer"
echo "=============================="

# Create directory
sudo mkdir -p /opt/adsb-telegram-bot
cd /opt/adsb-telegram-bot

# Download files
echo "📥 Downloading files..."
sudo curl -sL -o bot.py https://raw.githubusercontent.com/bersuc/adsb-telegram-bot/main/bot.py
sudo curl -sL -o config.py https://raw.githubusercontent.com/bersuc/adsb-telegram-bot/main/config.py

# Make executable
sudo chmod +x bot.py

# Create symlink
sudo ln -sf /opt/adsb-telegram-bot/bot.py /usr/local/bin/adsb-bot

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "Next steps:"
echo "   1. Edit the configuration file:"
echo "      nano /opt/adsb-telegram-bot/config.py"
echo ""
echo "   2. Run the bot:"
echo "      python3 /opt/adsb-telegram-bot/bot.py"
echo ""
echo "For updates, just run this installer again."