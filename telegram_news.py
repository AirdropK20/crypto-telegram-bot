print("🔥 RSS telegram_news.py IS NOW RUNNING 🔥")

import os
import requests
import hashlib
import xml.etree.ElementTree as ET

# =====================
# TELEGRAM CONFIG
# =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = "last_hash.txt"

# =====================
# RSS FEEDS (FREE)
# =====================
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    # Optional (uncomment if you want more)
    # "https://www.theblock.co/rss.xml",
    # "https://decrypt.co/feed"
]

# =====================
# KEYWORDS
# =====================
BREAKING_KEYWORDS = [
    "breaking", "urgent", "emergency",
    "halt", "halted", "paused", "suspended",
    "hack", "hacked", "exploit", "breach",
    "attack", "drained", "compromised",
    "outage", "downtime",
    "sec", "lawsuit", "court",
    "approval", "rejection", "ban",
    "bankruptcy", "liquidation", "insolvent"
]

UPDATE_KEYWORDS = [
    "update", "confirms", "confirmed",
    "statement", "responds", "response",
    "resumes", "restored", "reopened"
]

# =====================
# HELPERS
# =====================
def pick_label(title):
    t = title.lower()
    if any(k in t for k in BREAKING_KEYWORDS):
        return "BREAKING"
    if any(k in t for k in UPDATE_KEYWORDS):
        return "UPDATE"
    return ""

def pick_emoji(title):
    t = title.lower()
    if any(k in t for k in ["hack", "exploit", "breach", "attack"]):
        return "🚨"
    if any(k in t for k in ["sec", "court", "lawsuit"]):
        return "🏛️"
    if any(k in t for k in ["halt", "paused", "outage"]):
        return "⚠️"
    if "update" in t:
        return "🔄"
    return "🔹"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }, timeout=10)
    print("TELEGRAM STATUS:", r.status_code)

def get_last_hash():
    if not os.path.exists(STATE_FILE):
        return ""
    return open(STATE_FILE).read().strip()

def save_hash(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)

# =====================
# FETCH RSS
# =====================
def fetch_rss():
    items = []
    for feed in RSS_FEEDS:
        try:
            r = requests.get(feed, timeout=10)
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                source = feed.split("//")[1].split("/")[0]
                items.append({
                    "title": title,
                    "url": link,
                    "source": source
                })
        except Exception as e:
            print("RSS error:", e)
    return items

# =====================
# MAIN
# =====================
def main():
    last_hash = get_last_hash()
    news = fetch_rss()

    for item in news:
        title = item["title"]
        url = item["url"]
        source = item["source"]

        label = pick_label(title)
        if label not in ["BREAKING", "UPDATE"]:
            continue

        h = hashlib.md5(f"{title}{url}".lower().encode()).hexdigest()
        if h == last_hash:
            return

        emoji = pick_emoji(title)
        message = (
            f"{emoji} {label}: {title}\n\n"
            f"Source: {source}\n"
            f"{url}"
        )

        send_telegram(message)
        save_hash(h)
        return

if __name__ == "__main__":
    main()
