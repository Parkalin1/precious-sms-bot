import os
import requests
import time
from threading import Thread
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
HERO_KEY = os.environ.get("HERO_KEY")

if HERO_KEY:
    HERO_KEY = HERO_KEY.strip()

API = f"https://api.telegram.org/bot{TOKEN}"

DOMAINS = [
    "https://api.sms-activate.org/stubs/handler_api.php",
    "https://api.sms-activate.ae/stubs/handler_api.php",
    "https://sms-activate.org/stubs/handler_api.php",
    "https://api.smshero.com/stubs/handler_api.php"
]

def send_message(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=15)
    except:
        pass

def hero_api(action):
    if not HERO_KEY:
        return "HERO_KEY NOT SET"
    last = ""
    for d in DOMAINS:
        try:
            r = requests.get(f"{d}?api_key={HERO_KEY}&{action}", timeout=15)
            txt = r.text.strip()
            print(f"{d} => {txt[:150]}")
            if txt and "<html" not in txt.lower():
                return txt
            last = txt[:100]
        except Exception as e:
            last = str(e)[:100]
            continue
    return f"All failed: {last}"

def bot_loop():
    print("BOT LIVE")
    offset = 0
    orders = {}
    while True:
        try:
            res = requests.get(f"{API}/getUpdates?offset={offset}&timeout=30", timeout=35).json()
            for u in res.get("result", []):
                offset = u["update_id"] + 1
                if "message" not in u:
                    continue
                cid = u["message"]["chat"]["id"]
                txt = u["message"].get("text", "").strip()

                if txt.startswith("/start"):
                    send_message(cid, "<b>Bot LIVE ✅</b>\n\n/balance\n/buy\n/buy wa 0\n/code\n/cancel")

                elif "/balance" in txt:
                    b = hero_api("action=getBalance")
                    send_message(cid, f"Balance: <code>{b}</code>")

                elif txt.startswith("/buy"):
                    p = txt.split()
                    s = p[1] if len(p) > 1 else "wa"
                    c = p[2] if len(p) > 2 else "19"
                    if s == "ng":
                        s = "wa"
                        c = "19"
                    send_message(cid, f"Buying {s} {c}...")
                    r = hero_api(f"action=getNumber&service={s}&country={c}")
                    if "ACCESS_NUMBER" in r:
                        _, oid, num = r.split(":")
                        orders[cid] = oid
                        send_message(cid, f"✅ Number: <code>{num}</code> ID:{oid} -> /code")
                    else:
                        send_message(cid, f"❌ <code>{r}</code>")

                elif txt.startswith("/code"):
                    oid = orders.get(cid)
                    if not oid:
                        send_message(cid, "No order, /buy first")
                    else:
                        s = hero_api(f"action=getStatus&id={oid}")
                        if "STATUS_OK" in s:
                            send_message(cid, f"CODE: <code>{s.split(':')[1]}</code>")
                        else:
                            send_message(cid, f"<code>{s}</code>")

                elif txt.startswith("/cancel"):
                    oid = orders.get(cid)
                    if oid:
                        hero_api(f"action=setStatus&status=8&id={oid}")
                        send_message(cid, "Cancelled")
                        orders.pop(cid, None)
        except Exception as e:
            print(e)
            time.sleep(2)

app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

Thread(target=bot_loop, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
