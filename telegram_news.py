print("🔥 THIS FILE IS RUNNING 🔥")

import os
import requests
import hashlib

# =====================
# ENVIRONMENT VARIABLES
# =====================
CRYPTOPANIC_KEY = os.getenv("CRYPTOPANIC_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = "last_hash.txt"

# =====================
# CORE FUNCTIONS
# =====================

def fetch_news():
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_KEY}&kind=news"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        print("CryptoPanic error:", r.status_code)
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

# =====================
# MAIN (FORCE TEST MODE)
# =====================

def main():
    print("=== FORCE TEST MODE STARTED ===")

    last_hash = get_last_hash()
    news = fetch_news()

    if not news:
        print("No news returned from CryptoPanic")
        return

    item = news[0]  # FORCE first item

    title = item.get("title", "NO TITLE")
    url = item.get("url", "")
    source = item.get("source", {}).get("title", "Source")

    h = hashlib.md5(title.lower().encode()).hexdigest()
    if h == last_hash:
        print("Duplicate detected, skipping")
        return

    message = (
        f"🧪 TEST ALERT\n\n"
        f"{title}\n\n"
        f"Source: {source}\n"
        f"{url}"
    )

    send_telegram(message)
    save_hash(h)

    print("=== TEST MESSAGE SENT ===")

if __name__ == "__main__":
    main()
