import os, requests, threading, time, json
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
SIM5 = os.environ.get("SIM5_KEY")
ADMIN = int(os.environ.get("ADMIN_ID", "0"))
BASE = "https://5sim.net/v1"
H = {"Authorization": f"Bearer {SIM5}"}
TG = f"https://api.telegram.org/bot{TOKEN}"
OPAY_DETAILS = "OPay: 7080149221\nName: Ajerenye Precious\nAfter payment, type amount you paid"
PRICE_NGN = 5000
EU = ["portugal","romania","estonia","poland","bulgaria","netherlands"]
DB_FILE = "balances.json"

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_db(data):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

def get_bal(uid):
    db = load_db()
    return db.get(str(uid), 0)

def add_bal(uid, amount):
    db = load_db()
    db[str(uid)] = db.get(str(uid), 0) + amount
    save_db(db)

def sub_bal(uid, amount):
    db = load_db()
    uid = str(uid)
    if db.get(uid, 0) >= amount:
        db[uid] -= amount
        save_db(db)
        return True
    return False

app = Flask(__name__)
@app.route('/')
def home():
    return "V15 PAID BOT ALIVE - Ajerenye Precious"

def tg_api(method, data):
    try:
        requests.post(f"{TG}/{method}", json=data, timeout=10)
    except:
        pass

def bot_loop():
    offset = 0
    pending_topup = {}
    while True:
        try:
            r = requests.get(f"{TG}/getUpdates", params={"offset": offset, "timeout": 25}, timeout=30).json()
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                if "message" in u:
                    msg = u["message"]
                    cid = msg["chat"]["id"]
                    uid = msg["from"]["id"]
                    text = msg.get("text", "")
                    if text.startswith("/start"):
                        bal = get_bal(uid)
                        kb = {"inline_keyboard": [[{"text": f"Wallet: {bal} NGN", "callback_data": "wallet"}], [{"text": "Buy Europe Number", "callback_data": "europe"}], [{"text": "Top Up Wallet", "callback_data": "topup"}]]}
                        tg_api("sendMessage", {"chat_id": cid, "text": f"Welcome PRO 5SIM Bot\n\nYour Balance: {bal} NGN\nPrice per number: {PRICE_NGN} NGN\n\nFund wallet before you buy.", "reply_markup": kb})
                    elif text.startswith("/approve") and uid == ADMIN:
                        try:
                            parts = text.split()
                            target_id = parts[1]
                            amount = int(parts[2])
                            add_bal(target_id, amount)
                            tg_api("sendMessage", {"chat_id": target_id, "text": f"Admin credited you {amount} NGN\nNew Balance: {get_bal(target_id)} NGN"})
                            tg_api("sendMessage", {"chat_id": cid, "text": f"Approved {amount} for {target_id}"})
                        except:
                            tg_api("sendMessage", {"chat_id": cid, "text": "Use: /approve USER_ID AMOUNT"})
                    elif str(uid) in pending_topup:
                        pending_topup.pop(str(uid))
                        tg_api("sendMessage", {"chat_id": ADMIN, "text": f"NEW TOPUP REQUEST\nFrom ID: {uid}\nAmount: {text} NGN\nTo approve: /approve {uid} {text}\nCheck OPay 7080149221 first!"})
                        tg_api("sendMessage", {"chat_id": cid, "text": "Request sent! Admin go confirm soon."})
                if "callback_query" in u:
                    cb = u["callback_query"]
                    cid = cb["message"]["chat"]["id"]
                    mid = cb["message"]["message_id"]
                    uid_cb = cb["from"]["id"]
                    data = cb["data"]
                    requests.post(f"{TG}/answerCallbackQuery", json={"callback_query_id": cb["id"]}, timeout=10)
                    if data == "wallet":
                        bal = get_bal(uid_cb)
                        kb = {"inline_keyboard": [[{"text": "Top Up", "callback_data": "topup"}], [{"text": "Buy Number", "callback_data": "europe"}]]}
                        tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"Your Wallet: {bal} NGN\nPrice: {PRICE_NGN} NGN", "reply_markup": kb})
                    elif data == "topup":
                        pending_topup[str(uid_cb)] = True
                        tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"TOP UP WALLET\n\nSend money to:\n{OPAY_DETAILS}\n\nAfter you pay, type AMOUNT you paid here (e.g 1500)"})
                    elif data == "europe":
                        bal = get_bal(uid_cb)
                        if bal < PRICE_NGN:
                            kb = {"inline_keyboard": [[{"text": "Fund Wallet Now", "callback_data": "topup"}]]}
                            tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"Insufficient balance!\nYou get: {bal} NGN\nYou need: {PRICE_NGN} NGN\n\nPay to OPay:\n7080149221\nAjerenye Precious", "reply_markup": kb})
                        else:
                            kb = {"inline_keyboard": [[{"text": c.title(), "callback_data": f"buy_{c}"}] for c in EU]}
                            tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"SELECT EUROPE:\nBalance: {bal} NGN", "reply_markup": kb})
                    elif data.startswith("buy_"):
                        c = data.replace("buy_", "")
                        if not sub_bal(uid_cb, PRICE_NGN):
                            tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": "Balance don finish. Fund wallet."})
                        else:
                            tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"Buying {c}... Deducted {PRICE_NGN} NGN"})
                            try:
                                order = requests.get(f"{BASE}/user/buy/activation/{c}/any/whatsapp", headers=H, timeout=15).json()
                                if "id" in order:
                                    kb = {"inline_keyboard": [[{"text": "Get Code", "callback_data": f"code_{order['id']}"}], [{"text": "Cancel & Refund", "callback_data": f"cancel_{order['id']}_{uid_cb}"}]]}
                                    tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"Number Bought!\nCountry: {c.title()}\nNumber: +{order['phone']}\nBalance left: {get_bal(uid_cb)} NGN", "reply_markup": kb})
                                else:
                                    add_bal(uid_cb, PRICE_NGN)
                                    tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"Error: {order}\nRefunded {PRICE_NGN} NGN"})
                            except:
                                add_bal(uid_cb, PRICE_NGN)
                                tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"Network error. {PRICE_NGN} refunded."})
                    elif data.startswith("code_"):
                        oid = data.replace("code_", "")
                        try:
                            chk = requests.get(f"{BASE}/user/check/{oid}", headers=H, timeout=10).json()
                            if chk.get("sms"):
                                tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"YOUR CODE: {chk['sms'][0]['code']}"})
                            else:
                                tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"Waiting... Status: {chk.get('status')}"})
                        except:
                            pass
                    elif data.startswith("cancel_"):
                        parts = data.split("_")
                        oid = parts[1]
                        owner = parts[2] if len(parts) > 2 else str(uid_cb)
                        requests.get(f"{BASE}/user/cancel/{oid}", headers=H)
                        add_bal(owner, PRICE_NGN)
                        tg_api("editMessageText", {"chat_id": cid, "message_id": mid, "text": f"Cancelled! {PRICE_NGN} NGN refunded."})
        except Exception as e:
            print(f"loop error {e}")
            time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))