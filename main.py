import os
import time
import threading
import requests
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PAYSTACK_KEY = os.getenv("PAYSTACK_SECRET", "").strip()

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

BASE = "https://5sim.net/v1"
user_orders = {}
pending_pay = {}

PRICES_NGN = {
    "usa": 5000,
    "canada": 4500,
    "argentina": 2500,
    "brazil": 2000,
    "england": 5000,
    "germany": 4000,
    "france": 3000,
    "netherlands": 3000,
    "spain": 4000,
    "poland": 4500,
    "sweden": 3000,
    "italy": 3000,
    "austria": 3000,
    "belgium": 3000
}

COUNTRY_MAP = {
    "usa": "usa",
    "canada": "canada",
    "argentina": "argentina",
    "brazil": "brazil",
    "england": "england",
    "uk": "england",
    "germany": "germany",
    "france": "france",
    "netherlands": "netherlands",
    "spain": "spain",
    "poland": "poland",
    "sweden": "sweden",
    "italy": "italy",
    "austria": "austria",
    "belgium": "belgium"
}

def get_headers():
    return {"Authorization": f"Bearer {os.getenv('SIM5_KEY','').strip()}", "Accept": "application/json"}

def buy_number(country):
    url = f"{BASE}/user/buy/activation/{country}/any/whatsapp"
    r = requests.get(url, headers=get_headers(), timeout=30)
    if r.status_code!= 200:
        raise Exception(f"5SIM Error {r.status_code}: {r.text[:300]}")
    return r.json()

def get_sms(order_id):
    url = f"{BASE}/user/check/{order_id}"
    r = requests.get(url, headers=get_headers(), timeout=20)
    return r.json()

def cancel_order(order_id):
    url = f"{BASE}/user/cancel/{order_id}"
    r = requests.get(url, headers=get_headers(), timeout=20)
    return r.text

def create_paystack_link(email, amount_naira, user_id, country):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {"Authorization": f"Bearer {PAYSTACK_KEY}", "Content-Type": "application/json"}
    data = {"email": email, "amount": int(amount_naira * 100), "metadata": {"user_id": str(user_id), "country": country}}
    r = requests.post(url, headers=headers, json=data, timeout=20)
    return r.json()

def verify_paystack(ref):
    url = f"https://api.paystack.co/transaction/verify/{ref}"
    headers = {"Authorization": f"Bearer {PAYSTACK_KEY}"}
    r = requests.get(url, headers=headers, timeout=20)
    return r.json()

@app.route("/")
def home():
    return "Bot is Live"

@bot.message_handler(commands=['start'])
def start(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🇺🇸 USA ₦5000"), types.KeyboardButton("🇨🇦 Canada ₦4500"))
    markup.add(types.KeyboardButton("🇦🇷 Argentina ₦2500"), types.KeyboardButton("🇧🇷 Brazil ₦2000"))
    markup.add(types.KeyboardButton("🇬🇧 UK ₦5000"), types.KeyboardButton("🇩🇪 Germany ₦4000"))
    markup.add(types.KeyboardButton("🇫🇷 France ₦3000"), types.KeyboardButton("🇳🇱 Netherlands ₦3000"))
    markup.add(types.KeyboardButton("🇪🇸 Spain ₦4000"), types.KeyboardButton("🇵🇱 Poland ₦4500"))
    markup.add(types.KeyboardButton("🇸🇪 Sweden ₦3000"), types.KeyboardButton("🇮🇹 Italy ₦3000"))
    markup.add(types.KeyboardButton("🇦🇹 Austria ₦3000"), types.KeyboardButton("🇧🇪 Belgium ₦3000"))
    markup.add(types.KeyboardButton("❌ Cancel"))
    bot.send_message(m.chat.id, "Welcome to Precious SMS!\n\nAmerica + Europe countries available.\nChoose country, pay with Paystack, get code sharp!", reply_markup=markup)

@bot.message_handler(commands=['cancel'])
def cancel_cmd(m):
    order_id = user_orders.get(m.chat.id)
    if not order_id:
        bot.send_message(m.chat.id, "No active order")
        return
    cancel_order(order_id)
    user_orders.pop(m.chat.id, None)
    bot.send_message(m.chat.id, "Cancelled!")

@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text.lower()
    if "cancel" in text:
        return cancel_cmd(m)
    country = None
    for key in COUNTRY_MAP:
        if key in text:
            country = COUNTRY_MAP[key]
            break
    if not country:
        return
    price = PRICES_NGN.get(country, 3000)
    bot.send_message(m.chat.id, f"You choose {country.upper()} - ₦{price}\n\nSend your EMAIL to generate Paystack link:")
    bot.register_next_step_handler(m, lambda msg: ask_email(msg, country, price))

def ask_email(m, country, price):
    email = m.text.strip()
    if "@" not in email:
        bot.send_message(m.chat.id, "Invalid email. Send correct email:")
        bot.register_next_step_handler(m, lambda msg: ask_email(msg, country, price))
        return
    bot.send_message(m.chat.id, "Generating Paystack link...")
    try:
        res = create_paystack_link(email, price, m.chat.id, country)
        if not res.get("status"):
            bot.send_message(m.chat.id, f"Paystack error: {res}")
            return
        link = res["data"]["authorization_url"]
        ref = res["data"]["reference"]
        pending_pay[ref] = {"user_id": m.chat.id, "country": country, "price": price}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Pay with Paystack", url=link))
        markup.add(types.InlineKeyboardButton("✅ I don pay - Verify", callback_data=f"verify_{ref}"))
        bot.send_message(m.chat.id, f"Pay ₦{price} for {country.upper()}:", reply_markup=markup)
    except Exception as e:
        bot.send_message(m.chat.id, f"Error: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data.startswith("verify_"):
        ref = call.data.split("verify_")[1]
        info = pending_pay.get(ref)
        if not info:
            bot.answer_callback_query(call.id, "Not found")
            return
        bot.send_message(call.message.chat.id, "Verifying payment...")
        v = verify_paystack(ref)
        if v.get("data") and v["data"].get("status") == "success":
            bot.send_message(call.message.chat.id, f"✅ Verified! Buying {info['country']}...")
            try:
                data = buy_number(info['country'])
                phone = data.get("phone")
                order_id = data.get("id")
                user_orders[call.message.chat.id] = order_id
                bot.send_message(call.message.chat.id, f"✅ Number: {phone}\nOrder: {order_id}\nWaiting for code...")
                pending_pay.pop(ref, None)
                for i in range(60):
                    time.sleep(5)
                    check = get_sms(order_id)
                    sms = check.get("sms")
                    if sms:
                        bot.send_message(call.message.chat.id, f"🔑 CODE: {sms}")
                        user_orders.pop(call.message.chat.id, None)
                        return
                bot.send_message(call.message.chat.id, "No code yet. /cancel")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"Error after payment: {e} Ref: {ref}")
        else:
            bot.send_message(call.message.chat.id, "❌ Payment not complete yet.")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except:
            time.sleep(5)