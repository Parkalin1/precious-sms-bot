import os, requests, time
from threading import Thread
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
SIM5 = (os.environ.get("SIM5_KEY") or os.environ.get("SMS_KEY") or "").strip()
API = f"https://api.telegram.org/bot{TOKEN}"
BASE = "https://5sim.net/v1"
HEADERS = {"Authorization": f"Bearer {SIM5}", "Accept": "application/json"}

COUNTRIES = {
    "usa": "USA",
    "england": "UK",
    "poland": "Poland Cheap",
    "canada": "Canada",
    "germany": "Germany",
    "nigeria": "Nigeria"
}

def send(cid, txt):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": cid, "text": txt, "parse_mode": "HTML"}, timeout=15)
    except:
        pass

def bot_loop():
    print("V12.1 FIXED STARTED")
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
                txt = u["message"].get("text", "").strip().lower()

                if txt.startswith("/start"):
                    send(cid, "<b>V12.1 5SIM LIVE</b>\n\n/countries\n/balance\n/buy whatsapp usa\n/buy whatsapp poland\n/code\n/cancel")

                elif "countries" in txt:
                    msg = "<b>Countries:</b>\n"
                    for k, v in COUNTRIES.items():
                        msg = msg + k + " - " + v + "\n"
                    msg = msg + "\nEx: /buy whatsapp usa"
                    send(cid, msg)

                elif "/balance" in txt:
                    try:
                        r = requests.get(BASE + "/user/profile", headers=HEADERS, timeout=15).json()
                        bal = r.get("balance", 0)
                        rating = r.get("rating", 0)
                        send(cid, f"Balance: ${bal} | Rating: {rating}")
                    except Exception as e:
                        send(cid, f"Balance error: {e}")

                elif txt.startswith("/buy"):
                    p = txt.split()
                    product = p[1] if len(p) > 1 else "whatsapp"
                    country = p[2] if len(p) > 2 else "usa"
                    if product == "wa":
                        product = "whatsapp"
                    if product == "tg":
                        product = "telegram"
                    send(cid, "Buying " + product + " " + country + "...")
                    try:
                        url = BASE + "/user/buy/activation/" + country + "/any/" + product
                        r = requests.get(url, headers=HEADERS, timeout=20).json()
                        print(r)
                        if "id" in r and "phone" in r:
                            oid = r["id"]
                            phone = r["phone"]
                            price = r.get("price", "?")
                            orders[cid] = oid
                            text = "OK " + country + "\nNumber: " + str(phone) + "\nID: " + str(oid) + "\nPrice: $" + str(price) + "\n\nWait 20s then /code"
                            send(cid, text)
                        else:
                            send(cid, "Failed: " + str(r)[:400] + "\nTry /buy whatsapp poland")
                    except Exception as e:
                        send(cid, "Error: " + str(e))

                elif txt.startswith("/code"):
                    oid = orders.get(cid)
                    if not oid:
                        send(cid, "No order. /buy first")
                    else:
                        try:
                            r = requests.get(BASE + "/user/check/" + str(oid), headers=HEADERS, timeout=15).json()
                            sms = r.get("sms", [])
                            if sms:
                                code = sms[0].get("code", "")
                                full = sms[0].get("text", "")
                                send(cid, "OTP: " + str(code) + "\n" + str(full))
                            else:
                                status = r.get("status", "WAIT")
                                send(cid, "Waiting... " + str(status) + " - try /code again")
                        except Exception as e:
                            send(cid, "Error: " + str(e))

                elif txt.startswith("/cancel"):
                    oid = orders.get(cid)
                    if oid:
                        try:
                            requests.get(BASE + "/user/cancel/" + str(oid), headers=HEADERS, timeout=15)
                        except:
                            pass
                        orders.pop(cid, None)
                        send(cid, "Cancelled")

        except Exception as e:
            print(f"ERR {e}")
            time.sleep(2)

app = Flask(__name__)

@app.route("/")
def home():
    return "5SIM FIXED OK"

Thread(target=bot_loop, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
