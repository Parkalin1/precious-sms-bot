import requests, time, os
from flask import Flask
from threading import Thread

BOT_TOKEN = os.environ.get"8969960572:AAGG4qrNG5UhfvdOLSJFI1bFStKrCAiAqIc"
SIM5_KEY = os.environ.get"eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MjI5NDMzMTgsImlhdCI6MTc5MTQwNzMxOCwicmF5IjoiMTAxZTUyMTVkMmI2MDU5MTE3YzU2ZTE2NGRiYTQ4ZGUiLCJzdWIiOjQ1NTUwMjF9.tqHVBd4NL4Wwi8nXRNrmjvpeUT-qb3pgxnz-YLt68YWjp_xEqLrjMZIiKmC_zK6TlFAN2-9M8J522X-eDu7ENeuhFE9gpwS_qlq09K8sVakx5-Mot3jLDQbsRka5OaOzuyN3SuhUL96ijUAHOvR9evCPOQjUsKCsO1R30gAywy1Tj2ZrLHtbT6qcYHzLQYfGE3tU2msuuRN2P8UNg00Z5h-QD1olqgy1I-BG2sqxYPMwNn-tOc6yCmaWJdebxQCxztlcIspV9S8xC5o_JCXqjhuePFEMrtMMNiCWo_aKgXoEdhYzvv4dK4Bu40QfXVnkoeo0jHj0BxlDFT_9B8HcWg"

BASE = "https://5sim.net/v1"
HEAD = {"Authorization": "Bearer " + str(SIM5_KEY), "Accept": "application/json"}
BOT_URL = "https://api.telegram.org/bot" + str(BOT_TOKEN)

def send(chat_id, text):
    try:
        requests.post(BOT_URL + "/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except: pass

def bot_loop():
    print("Bot Running on Server...")
    offset = 0
    while True:
        try:
            r = requests.get(BOT_URL + "/getUpdates", params={"offset": offset, "timeout": 20}, timeout=35).json()
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message", {})
                chat = msg.get("chat", {}).get("id")
                text = msg.get("text", "").lower().strip()
                if not chat: continue
                if text in ["/start", "start", "hi"]:
                    send(chat, "✅ Bot Online 24/7!\n/balance - check balance\n/buy - buy number\n/check_ID - check OTP")
                elif "balance" in text:
                    try:
                        d = requests.get(BASE + "/user/profile", headers=HEAD, timeout=15).json()
                        send(chat, f"Balance: ${d.get('balance','0')}")
                    except Exception as e:
                        send(chat, f"Error: {e}")
                elif "buy" in text:
                    try:
                        send(chat, "Buying...")
                        d = requests.get(BASE + "/user/buy/activation/nigeria/any/whatsapp", headers=HEAD, timeout=20).json()
                        if "id" in d:
                            send(chat, f"SUCCESS!\nNumber: {d['phone']}\nID: {d['id']}\nCheck: /check_{d['id']}")
                        else:
                            send(chat, f"Failed: {d}")
                    except Exception as e:
                        send(chat, f"Buy error: {e}")
                elif text.startswith("/check_"):
                    oid = text.replace("/check_", "").strip()
                    try:
                        d = requests.get(BASE + "/user/check/" + oid, headers=HEAD, timeout=15).json()
                        sms = d.get('sms')
                        if sms:
                            code = sms[0].get('code') if isinstance(sms, list) else str(sms)
                            send(chat, f"OTP: {code}")
                        else:
                            send(chat, f"No SMS yet. Status: {d.get('status')}")
                    except Exception as e:
                        send(chat, f"Check error: {e}")
        except Exception as e:
            print("Loop error:", e)
            time.sleep(5)

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Running 24/7!"

if __name__ == "__main__":
    Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
