import os, requests, time
from threading import Thread
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
SIM5_KEY = os.environ.get("SIM5_KEY")
API = f"https://api.telegram.org/bot{TOKEN}"

def send_msg(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=15)
    except: pass

def get_balance():
    try:
        h = {"Authorization": f"Bearer {SIM5_KEY}", "Accept": "application/json"}
        r = requests.get("https://5sim.net/v1/user/profile", headers=h, timeout=15).json()
        return f"${r.get('balance',0)}"
    except Exception as e:
        return f"Error {e} | Key set: {bool(SIM5_KEY)}"

def bot_loop():
    print(f"BOT STARTED - Token:{bool(TOKEN)} SIM5:{bool(SIM5_KEY)}")
    offset=0
    while True:
        try:
            res = requests.get(f"{API}/getUpdates?offset={offset}&timeout=30", timeout=35).json()
            for u in res.get("result",[]):
                offset = u["update_id"]+1
                if "message" not in u: continue
                cid = u["message"]["chat"]["id"]
                txt = u["message"].get("text","")
                print("Got:", txt)
                if txt.startswith("/start"):
                    send_msg(cid, "<b>Precious SMS Bot LIVE ✅</b>\n\n/balance - check balance\n/buy ng - buy Nigeria number")
                elif "/balance" in txt:
                    bal = get_balance()
                    send_msg(cid, f"💰 Balance: {bal}")
                elif txt.startswith("/buy"):
                    send_msg(cid, "Send: /buy ng whatsapp\nExample: /buy usa telegram")
        except Exception as e:
            print("Err", e)
            time.sleep(2)

app = Flask(__name__)
@app.route("/")
def home(): return "OK"
Thread(target=bot_loop, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
