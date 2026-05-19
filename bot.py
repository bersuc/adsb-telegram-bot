import json
import math
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load configuration
try:
    from config import TOKEN, CHAT_ID, LAT_ANTENA, LON_ANTENA, BOT_NAME
except ImportError:
    print("❌ Error: Please create config.py based on config.example.py")
    exit(1)


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km using Haversine formula"""
    rad = math.pi / 180
    dlat = (lat2 - lat1) * rad
    dlon = (lon2 - lon1) * rad
    a = math.sin(dlat/2)**2 + math.cos(lat1*rad) * \
        math.cos(lat2*rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(6371 * c, 1)


def get_adsb_data():
    try:
        with open('/run/dump1090-fa/aircraft.json', 'r') as f:
            data = json.load(f)

        aircraft = data.get('aircraft', [])
        summary = []
        closest_flight = None
        min_distance = float('inf')

        for ac in aircraft:
            flight = ac.get('flight', '').strip(
            ) or f"HEX:{ac.get('hex', '').upper()}"
            altitude = ac.get('alt_baro')
            speed = ac.get('gs')
            lat = ac.get('lat')
            lon = ac.get('lon')

            # Ignore aircraft with incomplete data
            if not lat or not lon or altitude is None or speed is None:
                continue

            distance = calculate_distance(LAT_ANTENA, LON_ANTENA, lat, lon)
            dist_text = f"{distance} km"

            if distance < min_distance:
                min_distance = distance
                closest_flight = f"{flight} ({dist_text}, {altitude} ft, {speed} kt)"

            summary.append(
                f"✈️ **{flight}** | Dist: {dist_text} | Alt: {altitude} ft | Spd: {speed} kt")

        return len(summary), closest_flight, summary[:10]

    except Exception as e:
        return None, None, f"Error reading data: {e}"


async def radar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != CHAT_ID:
        return

    total, closest, summary = get_adsb_data()
    timestamp = datetime.now().strftime("%H:%M:%S")

    if total is None:
        await update.message.reply_text(f"❌ {summary}\n\n🕒 {timestamp}")
        return

    if total == 0:
        message = f"🛰️ **{BOT_NAME}**\n\nNo aircraft with complete data at the moment.\n🕒 {timestamp}"
    else:
        message = f"🛰️ **{BOT_NAME} - {timestamp}**\n\n"
        message += f"📊 **Monitored aircraft:** `{total}`\n"

        if closest:
            message += f"🎯 **Closest:** {closest}\n"

        message += "\n📋 **Identified flights:**\n"
        message += "\n".join(summary)

    await update.message.reply_text(message, parse_mode="Markdown")


def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("radar", radar_command))

    print(f"🤖 {BOT_NAME} started...")
    application.run_polling()


if __name__ == '__main__':
    main()
