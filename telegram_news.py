import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import sys

print("🚀 RSS Update-Only Bot Started")

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
NEW_ITEM_WINDOW_MINUTES = 15   # Only alert if RSS updated recently

# =====================
# RSS FEEDS
# =====================
RSS_FEEDS = {
    "Cointelegraph": "https://cointelegraph.com/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "The Block": "https://www.theblock.co/rss.xml",
    "Decrypt": "https://decrypt.co/feed"
}

# =====================
# AUTO-EMOJI LOGIC
# =====================
def pick_emoji(title: str) -> str:
    t = title.lower()

    if any(k in t for k in ["hack", "exploit", "breach", "drained"]):
        return "🚨"
    if any(k in t for k in ["sec", "lawsuit", "court", "regulator"]):
        return "🏛️"
    if any(k in t for k in ["bank", "blackrock", "fidelity"]):
        return "🏦"
    if any(k in t for k in ["fx", "forex", "usd", "dollar"]):
        return "💱"
    if any(k in t for k in ["gold", "silver"]):
        return "🥇"
    if any(k in t for k in ["halt", "paused", "outage"]):
        return "⚠️"
    if any(k in t for k in ["etf", "approval"]):
        return "📈"

    return "🚨"

# =====================
# HELPERS
# =====================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }, timeout=10)

def parse_pubdate(pub):
    try:
        return datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z")
    except:
        return None

# =====================
# MAIN LOGIC (UPDATE-ONLY)
# =====================
now = datetime.now(timezone.utc)
alert_sent = False

for source, feed in RSS_FEEDS.items():
    if alert_sent:
        break

    try:
        r = requests.get(feed, timeout=10)
        root = ET.fromstring(r.content)

        # 🔹 ONLY CHECK LATEST 2 ITEMS
        items = root.findall(".//item")[:2]

        for item in items:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub = item.findtext("pubDate", "")

            if not title or not link:
                continue

            published = parse_pubdate(pub)
            if not published:
                continue

            age = (now - published).total_seconds() / 60
            print(f"Latest item age {int(age)} min:", title)

            # 🔒 ONLY ALERT IF RSS WAS UPDATED RECENTLY
            if age > NEW_ITEM_WINDOW_MINUTES:
                continue

            emoji = pick_emoji(title)

            message = (
                f"{emoji} BREAKING: {title}\n\n"
                f"Source: {source}\n"
                f"{link}"
            )

            send_telegram(message)
            print("Update alert sent")
            alert_sent = True
            break

    except Exception as e:
        print("RSS error:", e)

if not alert_sent:
    print("No new RSS updates")