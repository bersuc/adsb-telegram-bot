import json
import math
import socket

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_VERSION = "1.2.0"

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

try:
    from config import (
        TOKEN,
        CHAT_ID,
        LAT_ANTENA,
        LON_ANTENA,
        BOT_NAME,
        DISTANCE_UNIT,
    )
except ImportError:
    print("ERROR: config.py not found")
    raise SystemExit(1)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def escape_markdown(text):
    value = str(text)
    return (
        value.replace("\\", "\\\\")
        .replace("_", "\\_")
        .replace("*", "\\*")
        .replace("[", "\\[")
        .replace("`", "\\`")
    )


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.connect(("8.8.8.8", 80))
            return connection.getsockname()[0]
    except Exception:
        return "Unavailable"


def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", encoding="utf-8") as file:
            return round(float(file.read().strip()) / 1000, 1)
    except Exception:
        return None


def cpu_rating(temp):
    if temp is None:
        return "⚪ Unknown"
    if temp < 60:
        return "🟢 Cool"
    if temp <= 75:
        return "🟡 Warm"
    return "🔴 Hot"


def get_uptime():
    seconds = get_uptime_seconds()
    if seconds is None:
        return "Unknown"

    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    if days:
        return f"{days}d {hours}h"
    return f"{hours}h {minutes}m"


def get_uptime_seconds():
    try:
        with open("/proc/uptime", encoding="utf-8") as file:
            return float(file.readline().split()[0])
    except Exception:
        return None


def calculate_distance(lat1, lon1, lat2, lon2):
    radians = math.pi / 180.0
    delta_lat = (lat2 - lat1) * radians
    delta_lon = (lon2 - lon1) * radians
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1 * radians)
        * math.cos(lat2 * radians)
        * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    if str(DISTANCE_UNIT).lower() == "miles":
        return round(3958.8 * c, 1), "mi"
    return round(6371.0 * c, 1), "km"


def get_snr_rating(snr):
    if snr is None:
        return "⚪ Unknown"
    if snr >= 18:
        return "🟢 Excellent"
    if snr >= 12:
        return "🟡 Good"
    return "🔴 Weak"


def get_strong_signal_rating(value):
    if value is None:
        return "⚪ Unknown"
    if value < 0.5:
        return "🟡 Low"
    if value <= 5:
        return "🟢 Excellent"
    if value <= 10:
        return "🟡 Good"
    return "🔴 Too High"


def get_strong_signal_status(value):
    if value is None:
        return "unknown"
    if value < 0.5:
        return "low"
    if value <= 5:
        return "excellent"
    if value <= 10:
        return "good"
    return "too_high"


def get_receiver_health(snr, strong_percent, temp):
    snr_rating = get_snr_rating(snr)
    temp_rating = cpu_rating(temp)
    strong_status = get_strong_signal_status(strong_percent)

    if strong_status == "too_high" or snr_rating.startswith("🔴") or temp_rating.startswith("🔴"):
        return "🔴 Attention Needed"
    if strong_status == "low":
        return "🟡 Good"
    if snr_rating.startswith("🟡") or temp_rating.startswith("🟡") or strong_status == "good":
        return "🟡 Good"
    return "🟢 Excellent"


def _sum_numbers(value, default=0):
    if isinstance(value, list):
        if not value:
            return default
        try:
            return sum(int(item) for item in value)
        except Exception:
            return default

    if value is None:
        return default

    try:
        return int(value)
    except Exception:
        return default


# --------------------------------------------------
# METRICS
# --------------------------------------------------

def load_stats():
    try:
        with open("/run/dump1090-fa/stats.json", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return None


def get_receiver_metrics(stats):
    if not stats:
        return None

    try:
        minute = stats.get("last1min", {}).get("local", {})
        total = stats.get("total", {}).get("local", {})

        signal = minute.get("signal")
        noise = minute.get("noise")
        snr = round(abs(signal - noise),
                    1) if signal is not None and noise is not None else None

        accepted_total = _sum_numbers(total.get("accepted"), 0)
        strong = int(total.get("strong_signals", 0))
        minute_messages = _sum_numbers(minute.get("accepted"), 0)

        strong_percent = round((strong / accepted_total)
                               * 100, 2) if accepted_total > 0 else 0

        return {
            "signal": signal,
            "noise": noise,
            "snr": snr,
            "gain": minute.get("gain_db"),
            "minute_messages": minute_messages,
            "accepted": accepted_total,
            "strong": strong,
            "strong_percent": strong_percent,
        }
    except Exception:
        return None


# --------------------------------------------------
# AIRCRAFT
# --------------------------------------------------

def get_aircraft():
    try:
        with open("/run/dump1090-fa/aircraft.json", encoding="utf-8") as file:
            data = json.load(file)

        aircraft = data.get("aircraft", [])
        summary = []
        closest = None
        closest_distance = float("inf")

        for item in aircraft:
            latitude = item.get("lat")
            longitude = item.get("lon")
            if latitude is None or longitude is None:
                continue

            hex_code = str(item.get("hex", "")).upper()
            flight = str(item.get("flight", "")).strip(
            ) or f"HEX:{hex_code or 'UNKNOWN'}"
            altitude = item.get("alt_baro", "---")
            speed = item.get("gs", "---")

            distance, unit = calculate_distance(
                LAT_ANTENA, LON_ANTENA, latitude, longitude)

            if distance < closest_distance:
                closest_distance = distance
                closest = f"{flight} ({distance} {unit}, {altitude} ft)"

            summary.append(
                f"✈️ {flight} | {distance} {unit} | {altitude} ft | {speed} kt")

        return len(summary), closest, summary[:10]
    except FileNotFoundError:
        return None, None, "Receiver offline.\ndump1090-fa is not running."
    except Exception as error:
        return None, None, f"Error reading aircraft data: {error}"


# --------------------------------------------------
# COMMANDS
# --------------------------------------------------

def authorized(update):
    return update.effective_chat.id == CHAT_ID


def _format_bot_name():
    return escape_markdown(BOT_NAME)


def _format_version():
    version = str(BOT_VERSION)
    return version if version.startswith("v") else f"v{version}"


def get_receiver_quality(temp, snr, strong_percent, uptime_seconds):
    score = 0.0

    if temp is None:
        score += 0.5
    elif temp < 60:
        score += 1.0
    elif temp <= 75:
        score += 0.5

    if snr is None:
        score += 0.5
    elif snr >= 18:
        score += 1.0
    elif snr >= 12:
        score += 0.5

    if strong_percent is None:
        score += 0.5
    elif strong_percent < 0.5:
        score += 0.5
    elif strong_percent <= 5:
        score += 1.0
    elif strong_percent <= 10:
        score += 0.5

    if uptime_seconds is None:
        score += 0.5
    elif uptime_seconds >= 7 * 86400:
        score += 1.0
    elif uptime_seconds >= 24 * 3600:
        score += 0.5

    if score >= 3.5:
        return "⭐⭐⭐⭐⭐ Perfect"
    if score >= 2.75:
        return "⭐⭐⭐⭐ Very Good"
    if score >= 2.0:
        return "⭐⭐⭐ Good"
    if score >= 1.25:
        return "⭐⭐ Fair"
    return "⭐ Poor"


async def radar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        return

    total, closest, summary = get_aircraft()

    if total is None:
        await update.message.reply_text(escape_markdown(summary), parse_mode="Markdown")
        return

    message = [f"📡 {_format_bot_name()}", ""]
    message.append(f"📊 Aircraft tracked: {total}")

    if closest:
        message.extend(["", "🎯 Closest aircraft:", escape_markdown(closest)])

    if summary:
        message.extend(["", "📋 Visible flights:",
                       escape_markdown("\n".join(summary))])
    else:
        message.extend(["", "No aircraft currently tracked."])

    await update.message.reply_text("\n".join(message), parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        return

    stats = load_stats()
    if stats is None:
        await update.message.reply_text(
            "Receiver offline.\nNo receiver statistics available.",
            parse_mode="Markdown",
        )
        return

    metrics = get_receiver_metrics(stats)
    if metrics is None:
        await update.message.reply_text(
            "Receiver offline.\nNo receiver statistics available.",
            parse_mode="Markdown",
        )
        return

    ip = escape_markdown(get_local_ip())
    temp = get_cpu_temp()
    temp_rating = cpu_rating(temp)
    uptime = escape_markdown(get_uptime())
    uptime_seconds = get_uptime_seconds()
    health = get_receiver_health(
        metrics["snr"], metrics["strong_percent"], temp)
    quality = get_receiver_quality(
        temp, metrics["snr"], metrics["strong_percent"], uptime_seconds)
    gain = metrics["gain"]
    snr = metrics["snr"]
    signal = metrics["signal"]
    noise = metrics["noise"]
    minute_messages = metrics["minute_messages"]
    strong_percent = metrics["strong_percent"]

    temp_value = "Unavailable" if temp is None else f"{temp:.1f}°C"
    gain_value = "Auto" if gain is None else f"{float(gain):.1f} dB"
    snr_value = "Unavailable" if snr is None else f"{snr:.1f} dB"
    signal_value = "Unavailable" if signal is None else f"{signal:.1f} dBFS"
    noise_value = "Unavailable" if noise is None else f"{noise:.1f} dBFS"

    message = [
        "📡 Receiver Status",
        "",
        f"{health}",
        "",
        f"🌐 Local IP: {ip}",
        f"⏱️ Uptime: {uptime}",
        f"🌡️ CPU Temp: {temp_value} {temp_rating}",
        "",
        f"📶 Gain: {gain_value}",
        f"📶 RSSI: {signal_value}",
        f"🌫 Noise Floor: {noise_value}",
        "",
        f"📨 Last Minute Messages: {minute_messages:,}",
        "",
        f"📈 SNR: {snr_value}",
        get_snr_rating(snr),
        "",
        f"⚡ Strong Signal %: {strong_percent:.2f}%",
        get_strong_signal_rating(strong_percent),
        "",
        f"{quality}",
        "",
        f"📨 Messages accepted: {metrics['accepted']:,}",
        f"💥 Strong signals: {metrics['strong']:,}",
        "",
        "🔗 Local Map:",
        f"http://{ip}/tar1090/",
    ]

    await update.message.reply_text(
        "\n".join(message),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        return

    message = [
        f"🤖 {_format_bot_name()}",
        "",
        f"Version {_format_version()}",
        "",
        "Aircraft monitoring bot for:",
        "",
        "• PiAware",
        "• dump1090-fa",
        "• readsb",
        "",
        "Commands:",
        "",
        "/radar",
        "/status",
        "/about",
    ]

    await update.message.reply_text("\n".join(message), parse_mode="Markdown")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("radar", radar_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("about", about_command))

    print(f"{BOT_NAME} {_format_version()} started successfully")
    app.run_polling()


if __name__ == "__main__":
    main()
