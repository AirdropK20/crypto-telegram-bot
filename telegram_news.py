import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

print("🔥 GitHub-only RSS bot running")

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

RSS_FEEDS = {
    "Cointelegraph": "https://cointelegraph.com/rss",
    "The Block": "https://www.theblock.co/rss.xml",
    "Decrypt": "https://decrypt.co/feed"
}

# Minutes window to accept news
MAX_AGE_MINUTES = 15

BREAKING_KEYWORDS = [
    "breaking", "halt", "paused", "suspended",
    "hack", "exploit", "breach",
    "outage", "sec", "lawsuit",
    "approval", "ban", "bankruptcy"
]

def is_breaking(title):
    t = title.lower()
    return any(k in t for k in BREAKING_KEYWORDS)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }, timeout=10)

def parse_time(pub_date):
    try:
        return datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
    except:
        return None

now = datetime.now(timezone.utc)

for source, feed in RSS_FEEDS.items():
    try:
        r = requests.get(feed, timeout=10)
        root = ET.fromstring(r.content)

        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")

            if not title or not link:
                continue

            if not is_breaking(title):
                continue

            published = parse_time(pub_date)
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
            print("ALERT SENT")
            raise SystemExit

    except Exception as e:
        print("RSS error:", e)

print("No fresh breaking news")