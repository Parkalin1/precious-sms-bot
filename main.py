import requests, time, os
from flask import Flask
from threading import Thread

BOT_TOKEN = os.environ.get("8969960572:AAGG4qrNG5UhfvdOLSJFI1bFStKrCAiAqIc")
SIM5_KEY = os.environ.get("eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MjI5NDMzMTgsImlhdCI6MTc5MTQwNzMxOCwicmF5IjoiMTAxZTUyMTVkMmI2MDU5MTE3YzU2ZTE2NGRiYTQ4ZGUiLCJzdWIiOjQ1NTUwMjF9.tqHVBd4NL4Wwi8nXRNrmjvpeUT-qb3pgxnz-YLt68YWjp_xEqLrjMZIiKmC_zK6TlFAN2-9M8J522X-eDu7ENeuhFE9gpwS_qlq09K8sVakx5-Mot3jLDQb")

BASE = "https://5sim.net/v1"
HEAD = {"Authorization": "Bearer " + str(SIM5_KEY), "Accept": "application/json"}
BOT_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send(chat_id, text, buttons=None):
    try:
        data = {"chat_id": chat_id, "text": text}
        if buttons:
            data["reply_markup"] = {"keyboard": buttons, "resize_keyboard": True}
        requests.post(BOT_URL + "/sendMessage", json=data, timeout=10)
    except:
        pass

def bot_loop():
    print("Precious PRO Bot Running...")
    offset = 0
    active_orders = {} # chat_id -> order_id
    while True:
        try:
            r = requests.get(BOT_URL + "/getUpdates", params={"offset": offset, "timeout": 25}, timeout=40).json()
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message", {})
                chat = msg.get("chat", {}).get("id")
                text = msg.get("text", "").strip()
                if not chat: continue

                low = text.lower()

                if low in ["/start", "hi", "hello", "menu"]:
                    btns = [["💰 Balance", "📱 Buy Number"], ["📩 Check OTP", "❓ Help"]]
                    send(chat, "🔥 *PRECIOUS SMS BOT* 🔥\n\nWelcome!\nYour 24/7 OTP Plug!\n\nChoose below 👇", btns)

                elif "balance" in low or "💰" in text:
                    try:
                        d = requests.get(BASE + "/user/profile", headers=HEAD, timeout=15).json()
                        send(chat, f"💰 Your Balance: ${d.get('balance','0')}\n\nFund your 5sim.net wallet to buy numbers!")
                    except Exception as e:
                        send(chat, f"Error: {e}")

                elif "buy" in low or "📱" in text:
                    try:
                        send(chat, "⏳ Buying Nigeria WhatsApp number...")
                        d = requests.get(BASE + "/user/buy/activation/nigeria/any/whatsapp", headers=HEAD, timeout=20).json()
                        if "id" in d:
                            active_orders[chat] = d['id']
                            send(chat, f"✅ SUCCESS!\n\n📞 Number: `{d['phone']}`\n🆔 ID: `{d['id']}`\n\nUse am for WhatsApp now. I go auto check OTP for you.\nTap 📩 Check OTP to get code!")
                        else:
                            send(chat, f"❌ Failed: {d}\nCheck balance and try again.")
                    except Exception as e:
                        send(chat, f"Buy error: {e}")

                elif "check" in low or "📩" in text or low.startswith("/check"):
                    oid = None
                    if "/check_" in low:
                        oid = low.replace("/check_","").strip()
                    else:
                        oid = active_orders.get(chat)

                    if not oid:
                        send(chat, "You never buy number yet. Click 📱 Buy Number first!")
                        continue
                    try:
                        d = requests.get(BASE + f"/user/check/{oid}", headers=HEAD, timeout=15).json()
                        sms = d.get('sms')
                        if sms:
                            code = sms[0].get('code') if isinstance(sms, list) else str(sms)
                            send(chat, f"🎉 OTP RECEIVED!\n\n🔑 CODE: *{code}*\n\nFull SMS: {sms}")
                        else:
                            send(chat, f"⏳ No SMS yet...\nStatus: {d.get('status')}\nKeep checking - e go come soon!")
                    except Exception as e:
                        send(chat, f"Check error: {e}")

                elif "help" in low or "❓" in text:
                    send(chat, "❓ HOW TO USE:\n1. Fund 5sim.net wallet\n2. Click 📱 Buy Number\n3. Use number for WhatsApp\n4. Click 📩 Check OTP\n\n24/7 Support!")

        except Exception as e:
            print("Loop error:", e)
            time.sleep(5)

app = Flask(__name__)
@app.route('/')
def home():
    return "Precious PRO Bot Running 24/7!"

if __name__ == "__main__":
    Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
