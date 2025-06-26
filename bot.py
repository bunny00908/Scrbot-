import re
import aiohttp
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- EDIT THESE ---
API_ID = 1234567  # your api_id from my.telegram.org
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

SOURCE_GROUPS = [-1001234567890, -1002345678901]  # your group IDs
TARGET_CHANNEL = -1003456789012                  # your channel ID

MAIN_CHANNEL_LINK = "https://t.me/YOUR_MAIN_CHANNEL"
BACKUP_CHANNEL_LINK = "https://t.me/YOUR_BACKUP_CHANNEL"
# ------------------

app = Client("cc_scraper_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- BIN lookup function ---
async def get_bin_info(bin_number):
    url = f"https://bins.antipublic.cc/bins/{bin_number}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10, ssl=False) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "scheme": data.get("scheme", "UNKNOWN").upper(),
                        "type": data.get("type", "UNKNOWN").upper(),
                        "brand": data.get("brand", "UNKNOWN").upper(),
                        "bank": data.get("bank", "UNKNOWN"),
                        "country": data.get("country_name", "UNKNOWN"),
                        "flag": data.get("country_flag", "🌍"),
                    }
    except Exception as e:
        print(f"BIN lookup failed: {e}")
    return {
        "scheme": "UNKNOWN", "type": "UNKNOWN", "brand": "UNKNOWN",
        "bank": "UNKNOWN", "country": "UNKNOWN", "flag": "🌍"
    }

# --- Card extraction ---
def extract_credit_cards(text):
    pattern = r'(\d{13,19})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})'
    return re.findall(pattern, text or "")

# --- Formatting message ---
def format_card_message(cc, bin_info):
    card_number, month, year, cvv = cc
    bin_number = card_number[:6]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        "<b>Approved Scrapper</b>\n"
        "━━━━━━━━━━━━━\n"
        f"<b>CC</b>: <code>{card_number}|{month}|{year}|{cvv}</code>\n"
        f"<b>Status</b>: APPROVED ✅\n"
        f"<b>Gate</b>: Stripe Auth\n"
        "━━━━━━━━━━━━━\n"
        f"<b>Bin</b>: <code>{bin_number}</code>\n"
        f"<b>Country</b>: {bin_info['country']} {bin_info['flag']}\n"
        f"<b>Issuer</b>: {bin_info['bank']}\n"
        f"<b>Type</b>: {bin_info['type']} - {bin_info['brand']}\n"
        "━━━━━━━━━━━━━\n"
        f"<b>Time</b>: <code>{timestamp}</code>\n"
        "<b>Scrapped By</b>: Bᴜɴɴʏ\n"
        "━━━━━━━━━━━━━"
    )

@app.on_message(filters.chat(SOURCE_GROUPS))
async def cc_scraper(client, message):
    text = message.text or message.caption
    cards = extract_credit_cards(text)
    if not cards:
        return
    for cc in cards:
        bin_number = cc[0][:6]
        bin_info = await get_bin_info(bin_number)
        msg = format_card_message(cc, bin_info)
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👉 Main Channel", url=MAIN_CHANNEL_LINK),
                    InlineKeyboardButton("🔄 Backup Channel", url=BACKUP_CHANNEL_LINK),
                ]
            ]
        )
        await app.send_message(
            TARGET_CHANNEL,
            msg,
            parse_mode="HTML",
            reply_markup=keyboard
        )

print("Bot is running. Press Ctrl+C to stop.")
app.run()
