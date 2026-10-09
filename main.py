import requests, os, time
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("8969960572:AAGG4qrNG5UhfvdOLSJFI1bFStKrCAiAqIc")
KEY = os.environ.get("eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MjI5NDMzMTgsImlhdCI6MTc5MTQwNzMxOCwicmF5IjoiMTAxZTUyMTVkMmI2MDU5MTE3YzU2ZTE2NGRiYTQ4ZGUiLCJzdWIiOjQ1NTUwMjF9.tqHVBd4NL4Wwi8nXRNrmjvpeUT-qb3pgxnz-YLt68YWjp_xEqLrjMZIiKmC_zK6TlFAN2-9M8J522X-eDu7ENeuhFE9gpwS_qlq09K8sVakx5-Mot3jLDQb")
API = f"https://api.telegram.org/bot{TOKEN}"

def send(cid, txt):
    try:
        requests.post(API+"/sendMessage", json={"chat_id": cid, "text": txt, "parse_mode":"Markdown"}, timeout=15)
    except Exception as e:
        print("send err", e)

def loop():
    print("BOT STARTED - Waiting for messages...")
    offset = 0
    while True:
        try:
            r = requests.get(API+"/getUpdates", params={"offset": offset, "timeout": 20}, timeout=30).json()
            if not r.get("ok"):
                print("getUpdates fail", r)
                time.sleep(3)
                continue
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                chat = u["message"]["chat"]["id"]
                text = u["message"].get("text","")
                print(f"Got: {text} from {chat}")
                # ALWAYS REPLY
                reply = f"✅ PRO BOT ALIVE!\n\nYou sent: {text}\n\nCommands:\n/balance - check balance\n/buy - buy number"
                send(chat, reply)
        except Exception as e:
            print("LOOP ERROR", e)
            time.sleep(5)

app = Flask(__name__)
@app.route('/')
def home():
    return "BOT ALIVE"

Thread(target=loop, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
