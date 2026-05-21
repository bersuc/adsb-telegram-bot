#!/bin/bash
# ADS-B Telegram Bot Updater
# Version: 1.0

echo "🔄 ADS-B Telegram Bot Updater"
echo "============================"

# Stop the service
echo "⏹️  Stopping service..."
sudo systemctl stop adsb-telegram-bot.service

# Create backup of current bot file
echo "📦 Creating backup..."
sudo cp /home/pi/bot_adsb.py /home/pi/bot_adsb.py.bak 2>/dev/null || true

# Download latest version
echo "📥 Downloading latest bot file..."
sudo curl -sL -o /home/pi/bot_adsb.py https://raw.githubusercontent.com/bersuc/adsb-telegram-bot/main/bot.py

# Set permissions
sudo chown pi:pi /home/pi/bot_adsb.py
sudo chmod +x /home/pi/bot_adsb.py

# Start the service again
echo "▶️  Starting service..."
sudo systemctl start adsb-telegram-bot.service

echo ""
echo "✅ Update completed successfully!"
echo ""
echo "Service status:"
sudo systemctl status adsb-telegram-bot.service --no-pager -l
echo ""
echo "Last 20 logs:"
sudo journalctl -u adsb-telegram-bot.service -n 20 --no-pager
echo ""
echo "To see live logs: sudo journalctl -u adsb-telegram-bot.service -f"