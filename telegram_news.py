print("🔥 telegram_news.py STARTED 🔥")

import os
import requests
import hashlib
import xml.etree.ElementTree as ET

# =====================
# TELEGRAM CONFIG
# =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =====================
# STATE FILE (PERSISTED VIA GIT COMMIT)
# =====================
STATE_FILE = "sent_hashes.txt"
MAX_STORED = 200

# =====================
# RSS FEEDS
# =====================
RSS_FEEDS = {
    "Cointelegraph": "https://cointelegraph.com/rss",
    "The Block": "https://www.theblock.co/rss.xml",
    "Decrypt": "https://decrypt.co/feed",
    "Bitcoin Magazine": "https://bitcoinmagazine.com/.rss/full/"
}

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
# LABEL & EMOJI LOGIC
# =====================
def pick_label(title: str) -> str:
    t = title.lower()
    if any(k in t for k in BREAKING_KEYWORDS):
        return "BREAKING"
    if any(k in t for k in UPDATE_KEYWORDS):
        return "UPDATE"
    return ""

def pick_emoji(title: str) -> str:
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

# =====================
# STATE HANDLING
# =====================
def load_sent_hashes():
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def save_sent_hashes(hashes):
    hashes = hashes[-MAX_STORED:]
    with open(STATE_FILE, "w") as f:
        for h in hashes:
            f.write(h + "\n")

# =====================
# TELEGRAM SENDER
# =====================
def send_telegram(text: str):
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
    print("TELEGRAM STATUS:", r.status_code)

# =====================
# RSS FETCHER
# =====================
def fetch_rss():
    items = []
    for source, feed in RSS_FEEDS.items():
        try:
            r = requests.get(feed, timeout=10)
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                if title and link:
                    items.append({
                        "title": title,
                        "url": link,
                        "source": source
                    })
        except Exception as e:
            print(f"RSS ERROR [{source}]:", e)
    return items

# =====================
# MAIN LOGIC
# =====================
def main():
    sent_hashes = load_sent_hashes()
    sent_set = set(sent_hashes)

    news_items = fetch_rss()

    for item in news_items:
        title = item["title"]
        url = item["url"]
        source = item["source"]

        label = pick_label(title)
        if label not in ["BREAKING", "UPDATE"]:
            continue

        h = hashlib.sha256(f"{title}|{url}".lower().encode()).hexdigest()

        if h in sent_set:
            continue

        emoji = pick_emoji(title)
        message = (
            f"{emoji} {label}: {title}\n\n"
            f"Source: {source}\n"
            f"{url}"
        )

        send_telegram(message)

        sent_hashes.append(h)
        save_sent_hashes(sent_hashes)

        print("STATE UPDATED")
        return

    print("No new qualifying news.")

if __name__ == "__main__":
    main()