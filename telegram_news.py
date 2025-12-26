import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os

print("🚀 Telegram RSS Bot Started")

# =====================
# TELEGRAM CONFIG
# =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ TELEGRAM CONFIG MISSING")
    exit(1)

# =====================
# RSS FEEDS
# =====================
RSS_FEEDS = {
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt": "https://decrypt.co/feed",
    "The Block": "https://www.theblock.co/rss.xml"
}

# =====================
# SETTINGS
# =====================
MAX_AGE_MINUTES = 20   # Only news from last 20 minutes
SEND_TEST_ALERT = True  # <-- SET FALSE AFTER FIRST TEST

# =====================
# KEYWORDS
# =====================
BREAKING_KEYWORDS = [
    "breaking", "halt