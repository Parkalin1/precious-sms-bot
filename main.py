import os, requests, time
from threading import Thread
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
HERO_KEY = os.environ.get("HERO_KEY")

API = f"https://api.telegram.org/bot{TOKEN}"
SMS_API = "https://api.hero-sms.com/stubs/handler_api.php"

def send(chat_id, text):
    requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=15)

def hero(action):
    url = f"{SMS_API}?api_key={HERO_KEY}&{action}"
    try:
        r = requests.get(url, timeout=20).text.strip()
        print(f"HEROSMS: {action} => {r}")
        return r
    except Exception as e:
        return f"ERROR {e}"

def bot():
    print("SMSHero BOT STARTED")
    offset = 0
    orders = {} # chat_id: order_id

    while True:
        try:
            res = requests.get(f"{API}/getUpdates?offset={offset}&timeout=30", timeout=35).json()
            for u in res.get("result", []):
                offset = u["update_id"] + 1
                if "message" not in u: continue

                cid = u["message"]["chat"]["id"]
                text = u["message"].get("text","").strip()

                # /start
                if text.startswith("/start"):
                    send(cid, "<b>Welcome to Precious SMSHero Bot</b> ✅\n\n"
                              "/balance - Check money\n"
                              "/buy - Buy Nigeria WhatsApp (N19)\n"
                              "/buy wa 0 - Buy Russia ($0.15)\n"
                              "/code - Get OTP code\n"
                              "/cancel - Cancel and refund")

                # /balance
                elif text.startswith("/balance"):
                    b = hero("action=getBalance")
                    send(cid, f"💰 Balance: {b}")

                # /buy
                elif text.startswith("/buy"):
                    parts = text.split()
                    service = parts[1] if len(parts)>1 else "wa"
                    country = parts[2] if len(parts)>2 else "19"

                    send(cid, f"⏳ Buying {service} for country {country}... wait")
                    result = hero(f"action=getNumber&service={service}&country={country}")

                    if "ACCESS_NUMBER" in result:
                        _, oid, num = result.split(":")
                        orders[cid] = oid
                        send(cid, f"✅ <b>NUMBER:</b> <code>{num}</code>\n"
                                   f"ID: {oid}\n\n"
                                   f"Go put am for WhatsApp now.\n"
                                   f"Then send /code here to get OTP")
                    else:
                        send(cid, f"❌ Failed: {result}\nTry /buy wa 0 or check /balance")

                # /code
                elif text.startswith("/code") or text.startswith("/otp"):
                    oid = orders.get(cid)
                    if not oid:
                        send(cid, "You never buy number. Do /buy first")
                        continue
                    s = hero(f"action=getStatus&id={oid}")
                    if "STATUS_OK" in s:
                        code = s.split(":")[1]
                        send(cid, f"🎉 <b>CODE: <code>{code}</code></b>")
                    elif "STATUS_WAIT" in s:
                        send(cid, "⏳ OTP never come yet. Wait 10 secs then do /code again")
                    else:
                        send(cid, f"Status: {s}")

                # /cancel
                elif text.startswith("/cancel"):
                    oid = orders.get(cid)
                    if oid:
                        hero(f"action=setStatus&status=8&id={oid}")
                        send(cid, "Cancelled - money refunded")
                        orders.pop(cid)
                    else:
                        send(cid, "No order")

        except Exception as e:
            print("error", e)
            time.sleep(2)

app = Flask(__name__)
@app.route("/")
def home():
    return "SMSHero Bot Running"

Thread(target=bot, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
