import os
import requests
import time
from threading import Thread
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
SIM5_KEY = os.environ.get("SIM5_KEY") # Make sure you add this for Render Environment too!
API = f"https://api.telegram.org/bot{TOKEN}"

# SIM5 API base
SIM5_API = "https://api.sim5.net/v1"

def send_msg(chat_id, text, keyboard=None):
    try:
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if keyboard:
            data["reply_markup"] = keyboard
        requests.post(f"{API}/sendMessage", json=data, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")

def get_balance():
    try:
        r = requests.get(f"{SIM5_API}/balance?api_key={SIM5_KEY}", timeout=10).json()
        return r.get("balance", "0")
    except:
        return "Error"

def bot_run():
    print(f"BOT STARTED OK - Token loaded: {bool(TOKEN)}")
    offset = 0
    while True:
        try:
            r = requests.get(f"{API}/getUpdates?offset={offset}&timeout=30", timeout=35).json()
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                if "message" not in u: continue
                chat_id = u["message"]["chat"]["id"]
                txt = u["message"].get("text", "")
                print("MSG:", txt)

                if txt.startswith("/start"):
                    kb = {
                        "inline_keyboard": [
                            [{"text": "💰 Check Balance", "callback_data": "balance"}],
                            [{"text": "🛒 Buy Number", "callback_data": "buy"}]
                        ]
                    }
                    send_msg(chat_id, f"<b>Welcome Boss!</b>\n\nBot is LIVE ✅\n\nClick below:", kb)

                elif txt.startswith("/balance"):
                    bal = get_balance()
                    send_msg(chat_id, f"💰 Your SIM5 Balance: ${bal}")

            # Check callback queries (buttons)
            for u in r.get("result", []):
                if "callback_query" in u:
                    offset = u["update_id"] + 1
                    cq = u["callback_query"]
                    chat_id = cq["message"]["chat"]["id"]
                    data = cq["data"]
                    if data == "balance":
                        bal = get_balance()
                        send_msg(chat_id, f"💰 Balance: ${bal}")
                    elif data == "buy":
                        send_msg(chat_id, "To buy, use: /buy [country_code] e.g /buy ng\nSupported: ng, us, uk")

            # Handle /buy command logic here later
            if txt and txt.startswith("/buy"):
                parts = txt.split()
                if len(parts) < 2:
                    send_msg(chat_id, "Usage: /buy ng")
                else:
                    send_msg(chat_id, f"Ordering {parts[1]} number... (We go add full order logic next)")

        except Exception as e:
            print("Loop error:", e)
            time.sleep(3)

app = Flask(__name__)
@app.route("/")
def home():
    return "Bot Running - PRO Version"

Thread(target=bot_run, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
