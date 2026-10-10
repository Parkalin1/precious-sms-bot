import os, requests, time
from threading import Thread
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
SIM5 = (os.environ.get("SIM5_KEY") or os.environ.get("FIVESIM_KEY") or os.environ.get("SMS_KEY") or os.environ.get("5SIM_KEY") or "").strip()
API = f"https://api.telegram.org/bot{TOKEN}"
BASE = "https://5sim.net/v1"
HEADERS = {"Authorization": f"Bearer {SIM5}", "Accept": "application/json"}

def send(cid, txt):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": cid, "text": txt, "parse_mode": "HTML"}, timeout=15)
    except: pass

def bot_loop():
    print("V13 SIM5_KEY FIXED STARTED - KEY LEN:", len(SIM5))
    offset=0
    orders={}
    while True:
        try:
            res=requests.get(f"{API}/getUpdates?offset={offset}&timeout=30", timeout=35).json()
            for u in res.get("result",[]):
                offset=u["update_id"]+1
                if "message" not in u: continue
                cid=u["message"]["chat"]["id"]
                txt=u["message"].get("text","").strip()
                low=txt.lower()

                if low.startswith("/start"):
                    send(cid,"<b>V13 LIVE ✅ SIM5_KEY OK</b>\n\n/countries\n/balance\n/buy whatsapp usa\n/buy whatsapp poland\n/code\n/cancel")

                elif "countries" in low:
                    send(cid,"usa - USA\nengland - UK\npoland - Poland Cheap\ncanada - Canada\ngermany - Germany\nnigeria - Nigeria\n\nEx: /buy whatsapp usa")

                elif "/balance" in low:
                    try:
                        r=requests.get(BASE+"/user/profile", headers=HEADERS, timeout=15)
                        print(f"BALANCE RAW {r.status_code}: {r.text[:500]}")
                        if r.status_code==200:
                            j=r.json()
                            send(cid,f"Balance: ${j.get('balance')} | Rating {j.get('rating')}")
                        else:
                            send(cid,f"5SIM Error {r.status_code}: {r.text[:400]}\n\nYour SIM5_KEY wrong. Copy full key from 5sim.net Profile")
                    except Exception as e:
                        print("BAL ERROR", e)
                        send(cid,f"Balance error: {e}")

                elif low.startswith("/buy"):
                    p=low.split()
                    prod=p[1] if len(p)>1 else "whatsapp"
                    country=p[2] if len(p)>2 else "usa"
                    if prod=="wa": prod="whatsapp"
                    if prod=="tg": prod="telegram"
                    send(cid,f"Buying {prod} {country}...")
                    try:
                        url=BASE+f"/user/buy/activation/{country}/any/{prod}"
                        r=requests.get(url, headers=HEADERS, timeout=20)
                        print(f"BUY RAW {r.status_code}: {r.text[:500]}")
                        j=r.json() if r.status_code==200 else {}
                        if "id" in j:
                            orders[cid]=j["id"]
                            send(cid,f"✅ {country.upper()}\nNumber: {j.get('phone')}\nID: {j.get('id')}\nPrice: ${j.get('price')}\n\n/code")
                        else:
                            send(cid,f"Failed: {r.text[:500]}\nTry /buy whatsapp poland")
                    except Exception as e:
                        send(cid,f"Error: {e}")

                elif low.startswith("/code"):
                    oid=orders.get(cid)
                    if not oid: send(cid,"No order. First /buy")
                    else:
                        try:
                            r=requests.get(BASE+f"/user/check/{oid}", headers=HEADERS, timeout=15).json()
                            sms=r.get("sms",[])
                            if sms: send(cid,f"OTP: {sms[0].get('code')}\n{sms[0].get('text')}")
                            else: send(cid,f"Waiting... {r.get('status')} - try /code again")
                        except Exception as e: send(cid,f"Error: {e}")

                elif low.startswith("/cancel"):
                    oid=orders.get(cid)
                    if oid:
                        try: requests.get(BASE+f"/user/cancel/{oid}", headers=HEADERS, timeout=15)
                        except: pass
                        orders.pop(cid,None)
                        send(cid,"Cancelled ✅")
                    else:
                        send(cid,"No order to cancel")
        except Exception as e:
            print("LOOP ERROR", e)
            time.sleep(2)

app=Flask(__name__)
@app.route("/")
def home(): return "V13 OK - SIM5_KEY"
Thread(target=bot_loop,daemon=True).start()
app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
