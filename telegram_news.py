import os
import requests
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import hashlib
import random

print("🚀 Crypto Crown Alert Bot Running")

# =====================
# TELEGRAM CONFIG
# =====================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("Missing Telegram secrets")
    exit()

# =====================
# SETTINGS
# =====================
STATE_FILE = "alert_state.txt"
NEWS_WINDOW_MIN = 180          # 3 hours
COMMENTARY_CHANCE = 0.35       # 35% commentary

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
# STATE HANDLING
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
    if image:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {"photo": open(image, "rb")}
        data = {"chat_id": CHAT_ID, "caption": text}
        requests.post(url, files=files, data=data, timeout=10)
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)

# =====================
# PRICE FETCH
# =====================
def get_price(symbol):
    if symbol in ["BTCUSDT", "ETHUSDT"]:
        r = requests.get(
            f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}",
            timeout=10
        ).json()
        return float(r["price"])

    if symbol == "GOLD":
        return requests.get("https://api.metals.live/v1/spot/gold", timeout=10).json()[0]["gold"]

    if symbol == "SILVER":
        return requests.get("https://api.metals.live/v1/spot/silver", timeout=10).json()[0]["silver"]

# =====================
# CHART GENERATION (WITH WATERMARK)
# =====================
def generate_chart(symbol):
    if symbol in ["BTCUSDT", "ETHUSDT"]:
        klines = requests.get(
            f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=50",
            timeout=10
        ).json()
        prices = [float(k[4]) for k in klines]
    else:
        prices = [get_price(symbol)] * 30

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(prices, linewidth=2, color="#00ffcc")
    ax.set_title(symbol.replace("USDT", ""), fontsize=14)
    ax.grid(alpha=0.25)

    # WATERMARK
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

# =====================
# COMMENTARY ENGINE
# =====================
def brief_comment(topic):
    comments = {
        "BTC": [
            "Bitcoin stays boring.\nBoring is bullish.",
            "BTC volatility is back.\nPay attention.",
        ],
        "ETH": [
            "ETH keeps compounding quietly.\nNarratives lag.",
        ],
        "GOLD": [
            "Gold moves quietly.\nMacro always whispers first.",
        ],
        "SILVER": [
            "Silver wakes up late.\nBut when it moves, it moves fast.",
        ],
        "GENERAL": [
            "Quiet narratives print hardest.\nEvery cycle. 😆",
        ]
    }
    return random.choice(comments.get(topic, comments["GENERAL"]))

# =====================
# PRICE ALERT CHECK
# =====================
def check_price_alerts():
    for symbol, levels in PRICE_LEVELS.items():
        price = get_price(symbol)

        for lvl in levels:
            key = f"{symbol}_{lvl}"
            if price < lvl and key not in sent_state:
                chart = generate_chart(symbol)
                text = f"🚨 {symbol.replace('USDT','')} DROPS BELOW {lvl}\n\nPrice: {round(price,2)}"
                send_message(text, chart)
                save_state(key)
                return True
    return False

# =====================
# NEWS ALERT CHECK
# =====================
def check_news_alerts():
    now = datetime.now(timezone.utc)

    for source, feed in RSS_FEEDS.items():
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

            age = (now - published).total_seconds() / 60
            if age > NEWS_WINDOW_MIN:
                continue

            h = hashlib.md5(title.encode()).hexdigest()
            if h in sent_state:
                continue

            if random.random() < COMMENTARY_CHANCE:
                msg = brief_comment("GENERAL")
            else:
                msg = f"📰 {title}\n\n{link}"

            send_message(msg)
            save_state(h)
            return True
    return False

# =====================
# MAIN FLOW
# =====================
if check_price_alerts():
    exit()

if check_news_alerts():
    exit()

send_message("📊 Market Pulse: No major moves yet. Watching key levels.")