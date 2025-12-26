import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import sys
import random

print("🚀 10-Min Guaranteed Alert Bot Started")

# =====================
# TELEGRAM CONFIG
# =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Telegram secrets missing")
    sys.exit(0)

# =====================
# SETTINGS
# =====================
NEW_ITEM_WINDOW_MINUTES = 180
MAX_ITEMS_PER_FEED = 2

# =====================
# RSS FEEDS
# =====================
RSS_FEEDS = {
    "Cointelegraph": "https://cointelegraph.com/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "The Block": "https://www.theblock.co/rss.xml",
    "Decrypt": "https://decrypt.co/feed",
}

# =====================
# AUTO-EMOJI
# =====================
def pick_emoji(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["hack", "exploit", "breach"]):
        return "🚨"
    if any(k in t for k in ["sec", "lawsuit", "court"]):
        return "🏛️"
    if any(k in t for k in ["bank", "blackrock", "fidelity"]):
        return "🏦"
    if any(k in t for k in ["gold", "silver"]):
        return "🥇"
    if any(k in t for k in ["etf", "approval"]):
        return "📈"
    return "🚨"

# =====================
# CRYPTOROVER STYLE FORMAT
# =====================
def format_rover(title: str) -> str:
    t = title.strip()
    if any(k in t.lower() for k in ["bitcoin", "btc"]):
        t += " #Bitcoin $BTC"
    if any(k in t.lower() for k in ["ethereum", "eth"]):
        t += " #Ethereum $ETH"
    return t

# =====================
# TELEGRAM SEND
# =====================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }, timeout=10)

# =====================
# MARKET PULSE (FILLER)
# =====================
MARKET_PULSE_MESSAGES = [
    "📊 Market Pulse: Volatility remains elevated. Traders watching BTC structure closely. #Bitcoin",
    "📉 Market Pulse: Fear still dominates sentiment. Key support levels under watch. #Crypto",
    "📈 Market Pulse: Momentum building across majors. Breakout confirmation pending. #BTC",
    "⚠️ Market Pulse: Liquidity thinning ahead of macro catalysts. Stay alert.",
    "🔍 Market Pulse: Altcoins showing mixed strength. BTC dominance in focus.",
]

# =====================
# MAIN LOGIC
# =====================
now = datetime.now(timezone.utc)
alert_sent = False

# --- Try RSS first ---
for source, feed in RSS_FEEDS.items():
    if alert_sent:
        break
    try:
        r = requests.get(feed, timeout=10)
        root = ET.fromstring(r.content)
        items = root.findall(".//item")[:MAX_ITEMS_PER_FEED]

        for item in items:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub = item.findtext("pubDate", "")

            if not title or not link:
                continue

            try:
                published = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z")
            except:
                continue

            age = (now - published).total_seconds() / 60
            print(f"RSS age {int(age)} min:", title)

            if age > NEW_ITEM_WINDOW_MINUTES:
                continue

            emoji = pick_emoji(title)
            rover_title = format_rover(title)

            message = (
                f"{emoji} {rover_title}\n\n"
                f"Source: {source}\n"
                f"{link}"
            )

            send_telegram(message)
            print("News alert sent")
            alert_sent = True
            break

    except Exception as e:
        print("RSS error:", e)

# --- Fallback: Market Pulse ---
if not alert_sent:
    pulse = random.choice(MARKET_PULSE_MESSAGES)
    send_telegram(pulse)
    print("Market pulse sent")