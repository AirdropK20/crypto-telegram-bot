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
# COINTELEGRAPH KEYWORDS
# =====================

BREAKING_KEYWORDS = [
    # Exchange / Infrastructure
    "halt", "halted", "paused", "suspended",
    "withdrawals", "deposits disabled",
    "outage", "downtime",

    # Security / Exploits
    "hack", "hacked", "exploit", "breach",
    "drained", "compromised", "attack",
    "vulnerability",

    # Legal / Regulatory
    "sec", "lawsuit", "charged", "charges",
    "court ruling", "settlement", "fine",
    "banned", "ban", "approval", "rejection",

    # Financial Collapse
    "bankruptcy", "insolvent", "liquidation",
    "defaults", "restructuring",

    # Network Failure
    "chain halted", "network halted",
    "consensus failure", "rollback",

    # Emergency Language
    "breaking", "emergency", "urgent"
]

UPDATE_KEYWORDS = [
    "update", "confirms", "confirmed",
    "statement", "official statement",
    "clarifies", "responds", "response",
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

    if any(k in t for k in [
        "hack", "exploit", "breach",
        "drained", "attack", "compromised"
    ]):
        return "🚨"

    if any(k in t for k in [
        "sec", "lawsuit", "court",
        "approval", "rejection", "ban"
    ]):
        return "🏛️"

    if any(k in t for k in [
        "halt", "paused", "suspended",
        "outage", "downtime"
    ]):
        return "⚠️"

    if any(k in t for k in [
        "bankruptcy", "liquidation", "insolvent"
    ]):
        return "💥"

    if "update" in t:
        return "🔄"

    return "🔹"

# =====================
# CORE FUNCTIONS
# =====================

def fetch_news():
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_KEY}&kind=news"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return []
    return r.json().get("results", [])

def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    requests.post(url, json=payload, timeout=10)

def get_last_hash():
    if not os.path.exists(STATE_FILE):
        return ""
    return open(STATE_FILE).read().strip()

def save_hash(h: str):
    with open(STATE_FILE, "w") as f:
        f.write(h)

# =====================
# MAIN LOGIC
# =====================

def main():
    last_hash = get_last_hash()
    news = fetch_news()

    for item in news:
        title = item.get("title", "")
        url = item.get("url", "")
        source = item.get("source", {}).get("title", "Source")

        if not title or not url:
            continue

        label = pick_label(title)
        if label not in ["BREAKING", "UPDATE"]:
            continue

        h = hashlib.md5(title.lower().encode()).hexdigest()
        if h == last_hash:
            return

        emoji = pick_emoji(title)
        headline = f"{emoji} {label}: {title}"

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
