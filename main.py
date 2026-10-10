import requests
import os
import time
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("BOT_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

def send_msg(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        print(e)

def bot_run():
    print("BOT STARTED OK - Token loaded:", bool(TOKEN))
    offset = 0
    while True:
        try:
            r = requests.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 20}, timeout=25).json()
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                chat_id = u["message"]["chat"]["id"]
                txt = u["message"].get("text","")
                print("MSG:", txt)
                send_msg(chat_id, "BOT ALIVE! You said: " + txt)
        except Exception as e:
            print("Loop error:", e)
            time.sleep(3)

app = Flask(__name__)
@app.route("/")
def home():
    return "Bot Running"

Thread(target=bot_run, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
