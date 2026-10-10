import os, requests, time
from threading import Thread
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
HERO_KEY = os.environ.get("HERO_KEY")

API = f"https://api.telegram.org/bot{TOKEN}"

APIS = [
    "https://api.smshero.com/stubs/handler_api.php",
    "https://api.sms-activate.org/stubs/handler_api.php",
    "https://smshero.com/stubs/handler_api.php",
    "https://api.sms-activate.ae/stubs/handler_api.php"
]

def send(cid, txt):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": cid, "text": txt, "parse_mode": "HTML"}, timeout=15)
    except: pass

def hero_call(action):
    for base in APIS:
        try:
            url = f"{base}?api_key={HERO_KEY}&{action}"
            r = requests.get(url, timeout=15).text.strip()
            print(f"TRY {base} => {r[:150]}")
            if r and "Name or service" not in r and "HTTP" not in r[:10]:
                if "ACCESS_" in r or "STATUS_" in r or "BALANCE" in r or r.replace(".","",1).isdigit():
                    return r
                if len(r) < 200:
                    return r
        except Exception as e:
            print(f"fail {base}: {e}")
            continue
    return "ERROR: All API domains failed - check HERO_KEY"

def bot_loop():
    print("BOT LIVE WITH MULTI-API")
    offset=0
    orders={}
    while True:
        try:
            res = requests.get(f"{API}/getUpdates?offset={offset}&timeout=30", timeout=35).json()
            for u in res.get("result",[]):
                offset = u["update_id"]+1
                if "message" not in u: continue
                cid = u["message"]["chat"]["id"]
                txt = u["message"].get("text","").strip()

                if txt.startswith("/start"):
                    send(cid, "<b>Precious SMS Bot FIXED ✅</b>\n\n/balance - check money\n/buy - buy Nigeria number (19)\n/buy wa 0 - Russia cheap\n/code - get OTP\n/cancel - cancel")

                elif "/balance" in txt:
                    b = hero_call("action=getBalance")
                    send(cid, f"💰 Balance: {b}\n\nIf $0, you need fund am!")

                elif txt.startswith("/buy"):
                    parts = txt.split()
                    if len(parts)==2 and parts[1]=="ng":
                        service="wa"; country="19"
                    else:
                        service = parts[1] if len(parts)>1 else "wa"
                        country = parts[2] if len(parts)>2 else "19"

                    send(cid, f"⏳ Buying {service} country {country}...")
                    r = hero_call(f"action=getNumber&service={service}&country={country}")
                    if "ACCESS_NUMBER" in r:
                        _, oid, num = r.split(":")
                        orders[cid]=oid
                        send(cid, f"✅ Number: <code>{num}</code>\nID: {oid}\n\nUse am for WhatsApp then /code")
                    else:
                        send(cid, f"❌ {r}\n\nIf NO_BALANCE, fund $1 first. If NO_NUMBERS, try /buy wa 0")

                elif txt.startswith("/code"):
                    oid = orders.get(cid)
                    if not oid:
                        send(cid, "No order, do /buy first")
                    else:
                        s = hero_call(f"action=getStatus&id={oid}")
                        if "STATUS_OK" in s:
                            code = s.split(":")[1]
                            send(cid, f"🎉 CODE: <code>{code}</code>")
                        elif "WAIT" in s:
                            send(cid, "⏳ Waiting... try /code again after 10sec")
                        else:
                            send(cid, f"Status: {s}")

                elif txt.startswith("/cancel"):
                    oid = orders.get(cid)
                    if oid:
                        hero_call(f"action=setStatus&status=8&id={oid}")
                        send(cid, "Cancelled & refunded")
                        orders.pop(cid, None)

        except Exception as e:
            print("loop err", e)
            time.sleep(2)

app = Flask(__name__)
@app.route("/")
def home(): return "OK"
Thread(target=bot_loop, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
