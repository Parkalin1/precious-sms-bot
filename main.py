import os, requests, threading, time, json
from flask import Flask, request, jsonify
from flask_cors import CORS

TOKEN = os.environ.get("BOT_TOKEN")
SIM5 = os.environ.get("SIM5_KEY")
PAYSTACK = os.environ.get("PAYSTACK_SECRET")
ADMIN = int(os.environ.get("ADMIN_ID", "0"))
BASE = "https://5sim.net/v1"
H = {"Authorization": f"Bearer {SIM5}"}
TG = f"https://api.telegram.org/bot{TOKEN}"
OPAY_DETAILS = "OPay: 7080149221\nName: Ajerenye Precious\nAfter payment, type amount you paid"
PRICE_NGN = 5000
EU = ["portugal","romania","estonia","poland","bulgaria","netherlands"]
DB_FILE = "balances.json"

app = Flask(__name__)
CORS(app)

def load_db():
    try:
        with open(DB_FILE) as f: return json.load(f)
    except: return {}
def save_db(d):
    with open(DB_FILE,"w") as f: json.dump(f,d)

def tg_send(chat_id, text):
    try:
        requests.post(f"{TG}/sendMessage", json={"chat_id":chat_id,"text":text})
        return True
    except:
        return False

def buy_5sim():
    for country in EU:
        try:
            r = requests.get(f"{BASE}/user/buy/activation/country/{country}/operator/any/product/whatsapp", headers=H, timeout=20)
            if r.status_code == 200:
                return r.json()
        except: continue
    return None

def check_5sim(id):
    for _ in range(9):
        time.sleep(20)
        try:
            r = requests.get(f"{BASE}/user/check/{id}", headers=H, timeout=20).json()
            if r.get('sms'):
                return r['sms'][0]['code'], r.get('phone')
        except: continue
    return None

def verify_paystack(ref):
    r = requests.get(f"https://api.paystack.co/transaction/verify/{ref}", headers={"Authorization": f"Bearer {PAYSTACK}"}).json()
    return r.get('status') and r['data']['status']=='success', r.get('data')

def refund_paystack(trans_id):
    requests.post("https://api.paystack.co/refund", json={"transaction": trans_id}, headers={"Authorization": f"Bearer {PAYSTACK}"})

@app.route('/verify/<ref>')
def verify(ref):
    ok, data = verify_paystack(ref)
    if not ok:
        return jsonify({"status":"failed"})
    tg_user = data['metadata'].get('telegram')
    trans_id = data['id']
    bought = buy_5sim()
    if not bought:
        refund_paystack(trans_id)
        if tg_user: tg_send(tg_user, "❌ 5sim no get number now, your money don REFUND. Try again later.")
        return jsonify({"status":"refunded", "reason":"no number"})
    result = check_5sim(bought['id'])
    if not result:
        try: requests.get(f"{BASE}/user/cancel/{bought['id']}", headers=H)
        except: pass
        refund_paystack(trans_id)
        if tg_user: tg_send(tg_user, "❌ 5sim no give code, your money don REFUND.")
        return jsonify({"status":"refunded", "reason":"no sms"})
    code, phone = result
    sent = tg_send(tg_user, f"✅ Your WhatsApp Code\nNumber: {phone}\nCode: {code}\n\nUse am now!")
    if not sent:
        refund_paystack(trans_id)
        return jsonify({"status":"refunded", "reason":"telegram failed"})
    return jsonify({"status":"success", "phone":phone, "code":code})

@app.route('/')
def home(): return "Precious SMS Bot Live"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))