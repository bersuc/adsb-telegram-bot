#!/bin/bash
# ADS-B Telegram Bot Updater
# Version: 1.1

echo "🔄 ADS-B Telegram Bot Updater"
echo "============================"

# Stop the service
echo "⏹️  Stopping service..."
sudo systemctl stop adsb-telegram-bot.service

# Create backup of current bot.py
echo "📦 Creating backup..."
sudo cp /opt/adsb-telegram-bot/bot.py /opt/adsb-telegram-bot/bot.py.bak 2>/dev/null || true

# Download latest version
echo "📥 Downloading latest version..."
sudo curl -sL -o /opt/adsb-telegram-bot/bot.py https://raw.githubusercontent.com/bersuc/adsb-telegram-bot/main/bot.py

# Set permissions
sudo chown pi:pi /opt/adsb-telegram-bot/bot.py
sudo chmod +x /opt/adsb-telegram-bot/bot.py

# Restart the service
echo "▶️  Restarting service..."
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