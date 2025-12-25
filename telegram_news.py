print("=== SCRIPT STARTED ===")

import os
import requests
import hashlib

CRYPTOPANIC_KEY = os.getenv("CRYPTOPANIC_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = "last_hash.txt"

KEYWORDS = [
    "breaking", "exchange", "etf", "approval",
    "halt", "hack", "exploit", "inflow", "outflow"
]

def is_relevant(title):
    return any(k in title.lower() for k in KEYWORDS)

def fetch_news():
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_KEY}&kind=news"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return []
    return r.json().get("results", [])

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    r = requests.post(url, json=payload, timeout=10)
    print("TELEGRAM STATUS:", r.status_code)
    print("TELEGRAM RESPONSE:", r.text)

def get_last_hash():
    if not os.path.exists(STATE_FILE):
        return ""
    return open(STATE_FILE).read().strip()

def save_hash(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)

def main():
    last_hash = get_last_hash()
    news = fetch_news()

    for item in news:
        title = item.get("title", "")
        url = item.get("url", "")
        source = item.get("source", {}).get("title", "Source")

        if not title or not url or not is_relevant(title):
            continue

        h = hashlib.md5(title.encode()).hexdigest()
        if h == last_hash:
            return

emoji = pick_emoji(title)
label = pick_label(title)

if label:
    headline = f"{emoji} {label}: {title}"
else:
    headline = f"{emoji} {title}"

message = (
    f"{headline}\n\n"
    f"Source: {source}\n"
    f"{url}"
)

        send_telegram(message)
        save_hash(h)
        return

if __name__ == "__main__":
    main()

def pick_label(title):
    t = title.lower()

    if any(k in t for k in [
        "breaking", "hack", "exploit", "halt",
        "outage", "paused", "suspended",
        "bankruptcy", "liquidated"
    ]):
        return "BREAKING"

    if any(k in t for k in [
        "update", "resumes", "confirms",
        "clarifies", "statement", "response"
    ]):
        return "UPDATE"

    return ""
