import requests
import time
from telegram import Bot

# Config (birbaşa kodun içində)
TELEGRAM_TOKEN = "8021286101:AAGiyciV6KiQEGYj4YehSTTw24P-TTYGj7M"   # məsələn: 1234567890:ABC-xyz
CHAT_ID = "-1002968766741"   # kanal/chat id (rəqəmlə yazmaq daha dəqiqdir)
SOLSCAN_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3NTgzODU4NzIwMjMsImVtYWlsIjoiYmF5cmFtY2VzdXI1NjhAZ21haWwuY29tIiwiYWN0aW9uIjoidG9rZW4tYXBpIiwiYXBpVmVyc2lvbiI6InYyIiwiaWF0IjoxNzU4Mzg1ODcyfQ.fgergMSzCb8UgIec1IKehMybQldeP8fjpoUFR3F-q6A"
RPC_URL = "https://mainnet.helius-rpc.com/?api-key=76090032-b66d-4abf-821b-7532df3b6e0d

bot = Bot(token=TELEGRAM_TOKEN)

seen_tokens = {}


def fetch_new_tokens():
    url = "https://public-api.solscan.io/token/list?sortBy=createdAt&direction=desc&limit=10"
    headers = {"token": SOLSCAN_API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json().get("data", [])
    except Exception as e:
        print("Fetch error:", e)
    return []


def check_filters(token):
    top10_share = token.get("top10Share", 100)
    dex_paid = token.get("dexPaid", False)
    dev_tokens = token.get("devTokens", 999)
    socials = token.get("socials", {})

    if top10_share >= 20:
        return False
    if not dex_paid:
        return False
    if dev_tokens >= 10:
        return False
    if not (socials.get("tg") or socials.get("x") or socials.get("web")):
        return False
    return True


def format_message(token):
    msg = f"""{token.get('name')} ({token.get('url')}) | #{token.get('symbol')} | ${token.get('symbol')}
CA: {token.get('ca')}
├ 📊 MC: ${token.get('mc')}
├ 💬 Replies: {token.get('replies')}
├ 👤 DEV:
│        Tokens: {token.get('devTokens')} | KoTH: {token.get('koth')} | Complete: {token.get('complete')}
├ 🌐 Socials: TG ({token.get('socials', {}).get('tg')}) | X ({token.get('socials', {}).get('x')}) | WEB ({token.get('socials', {}).get('web')})
├ 🔊 Volume: ${token.get('volume')}
├ 📈 ATH: ${token.get('ath')}
├ 🧶 Bonding Curve: {token.get('bondingCurve')}%
├ 🔫 Snipers: {token.get('snipers')}
├ 👥 Holders: {token.get('holders')}
├ 👤 Dev hold: {token.get('devHold')}%
└ 🏆 Top 10 Holders: Σ {token.get('top10Share')}% \n{token.get('top10Distribution')}
DEX PAID"""
    return msg


def format_multiplier_message(token, mult, mc):
    ca = token.get("ca")
    symbol = token.get("symbol")
    link = f"https://solscan.io/token/{ca}"
    return f"🚀 {symbol} just hit {mult}x!\nMC: ${mc}\n🔗 {link}"


def process_tokens():
    tokens = fetch_new_tokens()
    for t in tokens:
        ca = t.get("ca")
        if not ca:
            continue

        if not check_filters(t):
            continue

        mc = t.get("mc", 0)

        if ca not in seen_tokens:
            seen_tokens[ca] = {"ath": mc, "next_mult": 2}
            bot.send_message(chat_id=CHAT_ID, text=format_message(t))
        else:
            if mc > seen_tokens[ca]["ath"]:
                seen_tokens[ca]["ath"] = mc

            ath = seen_tokens[ca]["ath"]
            next_mult = seen_tokens[ca]["next_mult"]
            if mc >= (ath * next_mult):
                bot.send_message(chat_id=CHAT_ID, text=format_multiplier_message(t, next_mult, mc))
                seen_tokens[ca]["next_mult"] += 1


if __name__ == "__main__":
    while True:
        process_tokens()
        time.sleep(30)
