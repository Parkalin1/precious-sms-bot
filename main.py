import requests
import os
import time
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("8969960572:AAGG4qrNG5UhfvdOLSJFI1bFStKrCAiAqIc")
API = "https://api.telegram.org/bot" + str(8969960572:AAGG4qrNG5UhfvdOLSJFI1bFStKrCAiAqIc)

def send_msg(chat_id, text):
    url = API + "/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=data, timeout=10)
    except:
        pass

def bot_run():
    print("BOT STARTED OK")
    offset = 0
    while True:
        try:
            url = API + "/getUpdates"
            params = {"offset": offset, "timeout": 20}
            resp = requests.get(url, params=params, timeout=25).json()
            for update in resp.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message", {})
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "")
                if chat_id:
                    print("Received:", text)
                    send_msg(chat_id, "BOT ALIVE! You said: " + text)
        except Exception as e:
            print("Error:", e)
            time.sleep(3)

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running"

if __name__ == "__main__":
    t = Thread(target=bot_run, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
