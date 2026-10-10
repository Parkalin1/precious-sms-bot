import os, requests, time
from threading import Thread
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
HERO_KEY = os.environ.get("HERO_KEY")
if HERO_KEY:
    HERO_KEY = HERO_KEY.strip()

API = f"https://api.telegram.org/bot{TOKEN}"
SMS_API = "https://smshero.com/stubs/handler_api.php"

def send(cid, txt):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": cid, "text": txt, "parse_mode": "HTML"}, timeout=15)
    except: pass

def hero_call(action):
    if not HERO_KEY:
        return "HERO_KEY NOT SET! Go Render -> Environment -> Add HERO_KEY"
    try:
        url = f"{SMS_API}?api_key={HERO_KEY}&{action}"
        r = requests.get(url, timeout=20)
        return r.text.strip()
    except Exception as e:
        return f"CONNECTION ERROR: {e}"

def bot_loop():
    print(f"BOT STARTED - TOKEN:{bool(TOKEN)} HERO_KEY:{bool(HERO_KEY)}")
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
                    status = f"YES {len(HERO_KEY)} chars" if HERO_KEY else "NO - NOT SET!"
                    send(cid, f"<b>DEBUG BOT</b>\nHERO_KEY: {status}\n\n/balance\n/buy\n/code\n/cancel")

                elif "/balance" in txt:
                    b = hero_call("action=getBalance")
                    send(cid, f"💰 Response: <code>{b}</code>")

                elif txt.startswith("/buy"):
                    p = txt.split()
                    if len(p)==2 and p[1]=="ng":
                        s="wa"; c="19"
                    else:
                        s = p[1] if len(p)>1 else "wa"
                        c = p[2] if len(p)>2 else "19"
                    send(cid, f"⏳ Buying {s} {c}...")
                    r = hero_call(f"action=getNumber&service={s}&country={c}")
                    if "ACCESS_NUMBER" in r:
                        _, oid, num = r.split(":")
                        orders[cid]=oid
                        send(cid, f"✅ <code>{num}</code> ID:{oid} -> /code")
                    else:
                        send(cid, f"❌ <code>{r}</code>")

                elif txt.startswith("/code"):
                    oid = orders.get(cid)
                    if not oid:
                        send(cid, "No order")
                    else:
                        s = hero_call(f"action=getStatus&id={oid}")
                        if "STATUS_OK" in s:
                            send(cid, f"🎉 <code>{s.split(':')[1]}</code>")
                        else:
                            send(cid, f"<code>{s}</code>")

                elif txt.startswith("/cancel"):
                    oid = orders.get(cid)
                    if oid:
                        hero_call(f"action=setStatus&status=8&id={oid}")
                        send(cid, "Cancelled")
                        orders.pop(cid, None)
        except Exception as e:
            print(e)
            time.sleep(2)

app = Flask(__name__)
@app.route("/")
def home(): return "OK"
Thread(target=bot_loop, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
