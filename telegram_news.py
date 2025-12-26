import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import sys
import random

print("🚀 CryptoRover Narrative + News Bot Started")

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
NEW_ITEM_WINDOW_MINUTES = 180   # 3 hours freshness
MAX_ITEMS_PER_FEED = 2          # only newest items
COMMENTARY_RATIO = 0.4          # 40% commentary, 60% news

# =====================
# RSS FEEDS
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
# AUTO-EMOJI
# =====================
def pick_emoji(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["hack", "exploit", "breach", "drained"]):
        return "🚨"
    if any(k in t for k in ["sec", "lawsuit", "court", "regulator"]):
        return "🏛️"
    if any(k in t for k in ["bank", "banks", "blackrock", "fidelity"]):
        return "🏦"
    if any(k in t for k in ["gold", "silver", "oil"]):
        return "🥇"
    if any(k in t for k in ["fx", "forex", "usd", "dollar"]):
        return "💱"
    if any(k in t for k in ["halt", "paused", "outage"]):
        return "⚠️"
    if any(k in t for k in ["etf", "approval", "inflows"]):
        return "📈"
    return "🚨"

# =====================
# CRYPTOROVER LENGTH FORMAT
# =====================
def format_cryptorover_length(title: str, max_len=120) -> str:
    t = title.strip()
    fillers = [
        "according to", "amid", "following",
        "after reports", "reportedly", "as per"
    ]
    lower = t.lower()
    for f in fillers:
        if f in lower:
            t = t[:lower.index(f)].strip()
            break
    if len(t) > max_len:
        t = t[:max_len].rsplit(" ", 1)[0]
    return t

# =====================
# SYMBOL ADDER
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
# NARRATIVE DETECTION
# =====================
def detect_narrative(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["rwa", "real world asset", "tokenization"]):
        return "RWA"
    if any(k in t for k in ["etf", "institutional", "inflows"]):
        return "INSTITUTIONS"
    if any(k in t for k in ["bitcoin", "btc"]):
        return "BITCOIN"
    if any(k in t for k in ["ethereum", "eth"]):
        return "ETH"
    if any(k in t for k in ["gold", "silver"]):
        return "MACRO"
    if any(k in t for k in ["meme", "memecoin"]):
        return "MEMES"
    return "GENERAL"

# =====================
# BRIEF COMMENTARY (YOUR STYLE)
# =====================
def generate_brief_comment(narrative: str) -> str:
    comments = {
        "RWA": [
            "RWA quietly won the year while everyone chased noise.\nBoring narratives print the hardest. 😆",
            "RWA keeps building while attention stays elsewhere.\nThat’s how real cycles start.",
        ],
        "INSTITUTIONS": [
            "Institutions position quietly.\nRetail notices later.",
            "Smart money doesn’t chase headlines.\nIt accumulates.",
        ],
        "BITCOIN": [
            "Bitcoin stays boring.\nBoring is bullish.",
            "BTC does its job.\nEverything else is noise.",
        ],
        "ETH": [
            "ETH compounds quietly.\nNarratives always lag price.",
        ],
        "MACRO": [
            "Macro shifts take time.\nMarkets price them first.",
        ],
        "MEMES": [
            "Memes grab attention.\nInfrastructure captures value.",
        ],
        "GENERAL": [
            "Quiet progress beats loud speculation.\nEvery cycle.",
        ],
    }
    return random.choice(comments[narrative])

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
# FALLBACK MARKET PULSE
# =====================
MARKET_PULSE = [
    "📊 Market Pulse: BTC consolidating near key levels.",
    "📉 Market Pulse: Sentiment remains cautious.",
    "📈 Market Pulse: Momentum building, breakout pending.",
    "⚠️ Market Pulse: Volatility elevated.",
]

# =====================
# MAIN LOGIC
# =====================
now = datetime.now(timezone.utc)
alert_sent = False

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
            if age > NEW_ITEM_WINDOW_MINUTES:
                continue

            narrative = detect_narrative(title)

            # Decide commentary vs news
            if random.random() < COMMENTARY_RATIO:
                message = generate_brief_comment(narrative)
            else:
                emoji = pick_emoji(title)
                short = format_cryptorover_length(title)
                short = add_symbols(short)
                message = f"{emoji} {short}\n\n{link}"

            send_telegram(message)
            print("Alert sent")
            alert_sent = True
            break

    except Exception as e:
        print("RSS error:", e)

# If no news → still send something
if not alert_sent:
    send_telegram(random.choice(MARKET_PULSE))
    print("Market pulse sent")