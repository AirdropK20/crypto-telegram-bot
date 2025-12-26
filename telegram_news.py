import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import sys

print("🚀 Telegram RSS Bot Started (GitHub-only)")

# =====================
# TELEGRAM CONFIG
# =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("⚠️ Telegram secrets missing, exiting safely")
    sys.exit(0)

# =====================
# RSS FEEDS
# =====================
RSS_FEEDS = {
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt": "https://decrypt.co/feed",
    "The Block": "https://www.theblock.co/rss.xml"
}

# =====================
# SETTINGS (IMPORTANT)
# =====================
MAX_AGE_MINUTES = 10   # VERY strict freshness window

# =====================
# KEYWORDS
# =====================
BREAKING_KEYWORDS = [
    "breaking", "halt", "paused", "suspended",
    "hack", "hacked", "exploit", "breach",
    "outage", "downtime",
    "sec", "lawsuit", "court",
    "approval", "ban", "bankruptcy"
]

# =====================
# HELPERS
# =====================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "disable_web_page_preview": False
        },
        timeout=10
    )
    print("Telegram status:", r.status_code)

def is_breaking(title):
    t = title.lower()
    return any(k in t for k in BREAKING_KEYWORDS)

def parse_pubdate(pub):
    try:
        return datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z")
    except:
        return None

# =====================
# MAIN LOGIC
# =====================
now = datetime.now(timezone.utc)
sent = False  # hard stop after first alert

for source, feed in RSS_FEEDS.items():
    if sent:
        break

    try:
        r = requests.get(feed, timeout=10)
        root = ET.fromstring(r.content)

        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub = item.findtext("pubDate", "")

            if not title or not link:
                continue

            if not is_breaking(title):
                continue

            published = parse_pubdate(pub)
            if not published:
                continue

            age_minutes = (now - published).total_seconds() / 60

            # 🔒 STRICT TIME GATE
            if age_minutes < 0 or age_minutes > MAX_AGE_MINUTES:
                continue

            message = (
                f"🚨 BREAKING: {title}\n\n"
                f"Source: {source}\n"
                f"{link}"
            )

            send_telegram(message)
            print("Breaking alert sent")
            sent = True
            break

    except Exception as e:
        print("RSS error:", e)

if not sent:
    print("No fresh breaking news")