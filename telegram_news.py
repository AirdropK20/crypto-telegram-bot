import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import sys
import random

print("🚀 CryptoRover-Style 10-Min Bot Started")

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
NEW_ITEM_WINDOW_MINUTES = 180     # News freshness window
MAX_ITEMS_PER_FEED = 2            # Check only latest items

# =====================
# RSS FEEDS (CRYPTO + MACRO)
# =====================
RSS_FEEDS = {
    "Cointelegraph": "https://cointelegraph.com/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "The Block": "https://www.theblock.co/rss.xml",
    "Decrypt": "https://decrypt.co/feed",
    "Bitcoin Magazine": "https://bitcoinmagazine.com/.rss/full/",
    "CryptoSlate": "https://cryptoslate.com/feed/",
    "Reuters Markets": "https://www.reuters.com/markets/rss",
}

# =====================
# AUTO-EMOJI LOGIC
# =====================
def pick_emoji(title: str) -> str:
    t = title.lower()

    if any(k in t for k in ["hack", "exploit", "breach", "drained", "attack"]):
        return "🚨"
    if any(k in t for k in ["sec", "lawsuit", "court", "regulator", "ban"]):
        return "🏛️"
    if any(k in t for k in ["bank", "banks", "blackrock", "fidelity", "vanguard"]):
        return "🏦"
    if any(k in t for k in ["fx", "forex", "usd", "dollar", "euro", "yen"]):
        return "💱"
    if any(k in t for k in ["gold", "silver", "oil"]):
        return "🥇"
    if any(k in t for k in ["halt", "paused", "suspended", "outage"]):
        return "⚠️"
    if any(k in t for k in ["etf", "approval", "approved", "inflows"]):
        return "📈"

    return "🚨"

# =====================
# CRYPTOROVER LENGTH FORMATTER
# =====================
def format_cryptorover_length(title: str, min_len=80, max_len=120) -> str:
    t = title.strip()

    fillers = [
        "according to", "report says", "amid",
        "following", "after reports",
        "reportedly", "as per"
    ]

    lower = t.lower()
    for f in fillers:
        if f in lower:
            t = t[:lower.index(f)].strip()
            break

    if len(t) > max_len:
        t = t[:max_len].rsplit(" ", 1)[0]

    if len(t) < min_len and ":" in t:
        t = t.split(":", 1)[1].strip()

    return t

# =====================
# SYMBOL / TAG ADDER
# =====================
def add_symbols(text: str) -> str:
    t = text.lower()
    tags = []

    if "bitcoin" in t or "btc" in t:
        tags += ["#Bitcoin", "$BTC"]
    if "ethereum" in t or "eth" in t:
        tags += ["#Ethereum", "$ETH"]

    clean = []
    for tag in tags:
        if tag not in clean:
            clean.append(tag)

    if clean:
        return f"{text} {' '.join(clean)}"

    return text

# =====================
# TELEGRAM SEND
# =====================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "disable_web_page_preview": False
        },
        timeout=10
    )

# =====================
# MARKET PULSE (FALLBACK)
# =====================
MARKET_PULSE = [
    "📊 Market Pulse: BTC consolidating near key levels.",
    "📉 Market Pulse: Sentiment remains cautious across crypto.",
    "📈 Market Pulse: Momentum building, breakout still pending.",
    "⚠️ Market Pulse: Volatility elevated ahead of macro events.",
    "🔍 Market Pulse: Altcoins mixed as BTC dominance holds."
]

# =====================
# MAIN LOGIC
# =====================
now = datetime.now(timezone.utc)
alert_sent = False

# --- Try RSS news first ---
for source, feed in RSS_FEEDS.items():
    if alert_sent:
        break

    try:
        r = requests.get(feed, timeout=10)
        root = ET.fromstring(r.content)
        items = root.findall(".//item")[:MAX_ITEMS_PER_FEED]

        for item in items:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub = item.findtext("pubDate", "")

            if not title or not link:
                continue

            try:
                published = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z")
            except:
                continue

            age = (now - published).total_seconds() / 60
            print(f"RSS age {int(age)} min:", title)

            if age > NEW_ITEM_WINDOW_MINUTES:
                continue

            emoji = pick_emoji(title)
            short_title = format_cryptorover_length(title)
            short_title = add_symbols(short_title)

            message = f"{emoji} {short_title}\n\n{link}"

            send_telegram(message)
            print("News alert sent")
            alert_sent = True
            break

    except Exception as e:
        print("RSS error:", e)

# --- Fallback: Market Pulse ---
if not alert_sent:
    pulse = random.choice(MARKET_PULSE)
    send_telegram(pulse)
    print("Market pulse sent")