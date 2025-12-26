import matplotlib
matplotlib.use("Agg")

import os
import requests
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import hashlib
import random
import sys

print("🚀 Crypto Crown Alert Bot Running")

# =====================
# TELEGRAM CONFIG
# =====================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ Missing Telegram secrets")
    sys.exit(0)

# =====================
# SETTINGS
# =====================
STATE_FILE = "alert_state.txt"
NEWS_WINDOW_MIN = 180
COMMENTARY_CHANCE = 0.35

# =====================
# PRICE LEVELS
# =====================
PRICE_LEVELS = {
    "BTCUSDT": [90000, 87000, 85000],
    "ETHUSDT": [4000, 3500, 3000],
    "GOLD": [2400, 2300],
    "SILVER": [30, 28]
}

# =====================
# RSS FEEDS
# =====================
RSS_FEEDS = {
    "Cointelegraph": "https://cointelegraph.com/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Reuters": "https://www.reuters.com/markets/rss"
}

# =====================
# STATE
# =====================
def load_state():
    if not os.path.exists(STATE_FILE):
        return set()
    return set(open(STATE_FILE).read().splitlines())

def save_state(key):
    with open(STATE_FILE, "a") as f:
        f.write(key + "\n")

sent_state = load_state()

# =====================
# TELEGRAM SEND
# =====================
def send_message(text, image=None):
    try:
        if image and os.path.exists(image):
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(image, "rb") as img:
                requests.post(
                    url,
                    files={"photo": img},
                    data={"chat_id": CHAT_ID, "caption": text},
                    timeout=15
                )
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(
                url,
                json={"chat_id": CHAT_ID, "text": text},
                timeout=15
            )
    except Exception as e:
        print("Telegram error:", e)

# =====================
# PRICE FETCH
# =====================
def get_price(symbol):
    try:
        if symbol in ["BTCUSDT", "ETHUSDT"]:
            r = requests.get(
                f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}",
                timeout=10
            ).json()
            return float(r["price"])

        if symbol == "GOLD":
            r = requests.get("https://api.metals.live/v1/spot/gold", timeout=10).json()
            return float(list(r[0].values())[0])

        if symbol == "SILVER":
            r = requests.get("https://api.metals.live/v1/spot/silver", timeout=10).json()
            return float(list(r[0].values())[0])

    except Exception as e:
        print("Price fetch error:", symbol, e)
        return None

# =====================
# CHART GENERATION
# =====================
def generate_chart(symbol):
    try:
        if symbol in ["BTCUSDT", "ETHUSDT"]:
            klines = requests.get(
                f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=50",
                timeout=10
            ).json()
            prices = [float(k[4]) for k in klines]
        else:
            price = get_price(symbol)
            prices = [price] * 30

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(prices, linewidth=2, color="#00ffcc")
        ax.set_title(symbol.replace("USDT", ""), fontsize=14)
        ax.grid(alpha=0.25)

        ax.text(
            0.99, 0.02,
            "@Crypto_Crown20",
            transform=ax.transAxes,
            fontsize=9,
            color="gray",
            alpha=0.6,
            ha="right",
            va="bottom"
        )

        filename = f"{symbol}.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()
        return filename

    except Exception as e:
        print("Chart error:", symbol, e)
        return None

# =====================
# PRICE ALERTS
# =====================
def check_price_alerts():
    for symbol, levels in PRICE_LEVELS.items():
        price = get_price(symbol)
        if not price:
            continue

        for lvl in levels:
            key = f"{symbol}_{lvl}"
            if price < lvl and key not in sent_state:
                chart = generate_chart(symbol)
                msg = f"🚨 {symbol.replace('USDT','')} DROPS BELOW {lvl}\n\nPrice: {round(price,2)}"
                send_message(msg, chart)
                save_state(key)
                return True
    return False

# =====================
# NEWS ALERTS
# =====================
def check_news_alerts():
    now = datetime.now(timezone.utc)

    for feed in RSS_FEEDS.values():
        try:
            r = requests.get(feed, timeout=10)
            root = ET.fromstring(r.content)
            items = root.findall(".//item")[:3]

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

                if (now - published).total_seconds() / 60 > NEWS_WINDOW_MIN:
                    continue

                h = hashlib.md5(title.encode()).hexdigest()
                if h in sent_state:
                    continue

                msg = f"📰 {title}\n\n{link}"
                send_message(msg)
                save_state(h)
                return True

        except Exception as e:
            print("RSS error:", e)

    return False

# =====================
# MAIN
# =====================
if check_price_alerts():
    sys.exit(0)

if check_news_alerts():
    sys.exit(0)

send_message("📊 Market Pulse: No major moves yet. Watching key levels.")