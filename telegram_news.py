import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import sys

print("🚀 Telegram RSS Bot Started")

# =====================
# TELEGRAM CONFIG
# =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Failsafe: do NOT crash workflow
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("⚠️ Telegram secrets not found, skipping run safely")
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
# SETTINGS
# =====================
MAX_AGE_MINUTES = 30      # Fresh news window
SEND_TEST_ALERT = False   # SET TO FALSE after first alert

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
# FORCE TEST ALERT
# =====================
if SEND_TEST_ALERT:
    send_telegram("✅ TEST ALERT: GitHub Actions → Telegram is WORKING")
    print("Test alert sent successfully")
    sys.exit(0)

# =====================
# MAIN RSS LOGIC
# =====================
now = datetime.now(timezone.utc)

for source, feed in RSS_FEEDS.items():
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

            age = (now - published).total_seconds() / 60
            if age > MAX_AGE_MINUTES:
                continue

            message = (
                f"🚨 BREAKING: {title}\n\n"
                f"Source: {source}\n"
                f"{link}"
            )

            send_telegram(message)
            print("Breaking alert sent")
            sys.exit(0)

    except Exception as e:
        print("RSS error:", e)

print("No fresh breaking news found")