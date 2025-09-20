import requests
from flask import Flask, request, jsonify
from telegram import Bot
import os

# Telegram konfiqurasiyası (Render env-dən oxuyuruq)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# API keys
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

BIRDEYE_API = "https://public-api.birdeye.so/public/market/price?address={}"
BIRDEYE_HEADERS = {"x-api-key": BIRDEYE_API_KEY}
HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/"

seen_tokens = set()
app = Flask(__name__)

# --- Token məlumatlarını çəkən funksiya ---
def fetch_token_info(ca):
    info = {"ca": ca}

    # Birdeye məlumatları
    try:
        r = requests.get(BIRDEYE_API.format(ca), headers=BIRDEYE_HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", {})
            info["symbol"] = data.get("symbol", "N/A")
            info["name"] = data.get("name", "N/A")
            info["price"] = data.get("value", 0)
            info["mc"] = data.get("mc", 0)
            info["liquidity"] = data.get("liquidity", 0)
    except Exception as e:
        print(f"Birdeye xətası: {e}")

    # Helius (top holders)
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenLargestAccounts",
            "params": [ca]
        }
        helius_url_with_key = f"{HELIUS_RPC_URL}?api-key={HELIUS_API_KEY}"
        r = requests.post(helius_url_with_key, json=payload, timeout=10)
        if r.status_code == 200:
            accounts = r.json().get("result", {}).get("value", [])
            if accounts:
                total_supply = sum([int(acc.get("amount", 0)) for acc in accounts]) or 1
                top10_share_amount = sum([int(acc.get("amount", 0)) for acc in accounts[:10]])

                info["holders"] = len(accounts)
                info["top10Share"] = (top10_share_amount / total_supply) * 100
                info["devHold"] = (int(accounts[0].get("amount", 0)) / total_supply) * 100
    except Exception as e:
        print(f"Helius xətası: {e}")

    return info

# --- Mesaj formatı ---
def format_message(token):
    return f"""✨ <b>YENİ TOKEN MINT EDİLDİ</b> ✨

<b>{token.get('name', 'N/A')} ({token.get('symbol', 'N/A')})</b>
CA: <code>{token.get('ca', 'N/A')}</code>

📊 <b>Market Cap:</b> ${token.get('mc', 0):,}
💰 <b>Dev Hold:</b> {token.get('devHold', 0):.2f}%
👥 <b>Holders:</b> {token.get('holders', 0):,}
📈 <b>Top 10 Share:</b> {token.get('top10Share', 0):.2f}%
💧 <b>Liquidity (DEX):</b> ${token.get('liquidity', 0):,.2f}

🔗 <a href="https://birdeye.so/token/{token.get('ca')}?chain=solana">Birdeye Link</a>
"""

# --- Webhook endpoint ---
@app.route("/helius-webhook", methods=["POST"])
def helius_webhook():
    data = request.json
    print("Yeni event:", data)

    try:
        for event in data.get("events", []):
            if event.get("type") == "TOKEN_MINT":
                ca = event.get("mint", "")
                if ca and ca not in seen_tokens:
                    token_data = fetch_token_info(ca)

                    # Filtrlər
                    if token_data.get("top10Share", 100) > 20:
                        continue
                    if token_data.get("liquidity", 0) <= 0:
                        continue
                    if token_data.get("holders", 0) > 10:
                        continue

                    bot.send_message(chat_id=CHAT_ID, text=format_message(token_data), parse_mode="HTML")
                    seen_tokens.add(ca)
    except Exception as e:
        print("Webhook işləmə xətası:", e)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
