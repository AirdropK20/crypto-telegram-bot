import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import sys

print("🚀 Telegram Macro + Crypto News Bot Started")

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
MAX_AGE_MINUTES = 360   # 6 hours (best balance for GitHub-only)

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
    "BeInCrypto": "https://beincrypto.com/feed/",
    "NewsBTC": "https://www.newsbtc.com/feed/"
}

# =====================
# KEYWORDS (EXPANDED)
# =====================
BREAKING_KEYWORDS = [
    # urgency
    "breaking", "urgent", "alert",

    # crypto core
    "bitcoin", "btc", "ethereum", "eth",
    "crypto", "cryptocurrency", "blockchain",

    # security / hacks
    "hack", "hacked", "exploit", "breach",
    "attack", "drained", "compromised",

    # exchanges / infra
    "exchange", "binance", "coinbase",
    "kraken", "okx", "bybit",
    "halt", "halted", "paused", "suspended",
    "outage", "downtime", "withdrawals",

    # regulation / legal
    "sec", "lawsuit", "court", "charged",
    "fine", "settlement", "ban", "banned",
    "regulator", "regulatory",

    # ETFs / products
    "etf", "spot etf", "approval", "approved",

    # financial stress
    "bankruptcy", "liquidation", "insolvent",
    "collapse", "defaults",

    # protocol / chain
    "network halted", "chain halted",
    "consensus failure", "rollback",

    # banks / tradfi
    "bank", "banks", "banking",
    "fed", "federal reserve",
    "ecb", "boj", "pboc",
    "interest rate", "rate hike", "rate cut",
    "inflation", "recession",

    # institutions
    "blackrock", "fidelity", "vanguard",
    "goldman", "jp morgan", "morgan stanley",
    "bank of america", "citigroup",

    # FX / FOREX
    "forex", "fx", "dollar", "usd",
    "eur", "euro", "yen", "jpy",
    "pound", "gbp", "currency",
    "devaluation", "depeg",

    # metals / commodities
    "gold", "silver",
    "commodities", "oil"
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

def is_relevant(title):
    t = title.lower()
    return any(k in t for k in BREAKING_KEYWORDS)

def parse_pubdate(pub):
    try:
        return datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z")
    except:
        return None

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

        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub = item.findtext("pubDate", "")

            if not title or not link:
                continue

            if not is_relevant(title):
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
            print("Alert sent")
            alert_sent = True
            break

    except Exception as e:
        print(f"RSS error [{source}]:", e)

if not alert_sent:
    print("No relevant news in time window")