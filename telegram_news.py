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

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Telegram secrets missing")
    sys.exit(0)

# =====================
# SETTINGS
# =====================
SEND_TEST_ALERT = False      # ← SET FALSE after you see test alert
MAX_AGE_MINUTES = 60        # 1 hour window (important for GitHub)

# =====================
# RSS FEEDS
# =====================
RSS_FEEDS = {
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt": "https://decrypt.co/feed",
    "The Block": "https://www.theblock.co/rss.xml"
}

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
    return any(k in title.lower() for k in BREAKING_KEYWORDS)

def parse_pubdate(pub):
    try:
        return datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z")
    except:
        return None

# =====================
# STEP 1: FORCE TEST ALERT
# =====================
if SEND_TEST_ALERT:
    send_telegram("✅ TEST ALERT: GitHub → Telegram is WORKING")
    print("Test alert sent. Disable SEND_TEST_ALERT now.")
    sys.exit(0)

# =====================
# STEP 2: REAL RSS LOGIC
# =====================
now = datetime.now(timezone.utc)
alert_sent = False

for source, feed in RSS_FEEDS.items():
    if alert_sent:
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

            age = (now - published).total_seconds() / 60
            print(f"Found news age {int(age)} min:", title)

            if age > MAX_AGE_MINUTES:
                continue

            message = (
                f"🚨 BREAKING: {title}\n\n"
                f"Source: {source}\n"
                f"{link}"
            )

            send_telegram(message)
            print("Breaking alert sent")
            alert_sent = True
            break

    except Exception as e:
        print("RSS error:", e)

if not alert_sent:
    print("No breaking news in time window")