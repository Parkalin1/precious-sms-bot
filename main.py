import os
import time
import json
import threading
import requests
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

BASE = "https://5sim.net/v1"
user_orders = {}

PRICES = {
    "usa": 2.0,
    "canada": 2.0,
    "argentina": 0.8,
    "brazil": 1.2
}

BAL_FILE = "balances.json"

def load_balances():
    if os.path.exists(BAL_FILE):
        try:
            with open(BAL_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_balances(data):
    with open(BAL_FILE, "w") as f:
        json.dump(data, f)

user_balances = load_balances()

def get_headers():
    return {
        "Authorization": f"Bearer {os.getenv('SIM5_KEY','').strip()}",
        "Accept": "application/json"
    }

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

@app.route("/")
def home():
    return "Bot is Live"

@bot.message_handler(commands=['start'])
def start(m):
    uid = str(m.chat.id)
    if uid not in user_balances:
        user_balances[uid] = 0.0
        save_balances(user_balances)
    bal = user_balances.get(uid, 0.0)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🇺🇸 USA $2.0", "🇨🇦 Canada $2.0")
    markup.add("🇦🇷 Argentina $0.8", "🇧🇷 Brazil $1.2")
    markup.add("💰 My Balance", "❌ Cancel")
    bot.send_message(m.chat.id, f"Welcome!\nYour Wallet: ${bal:.2f}\n\nChoose country:", reply_markup=markup)

@bot.message_handler(commands=['mybalance', 'balance'])
def mybal(m):
    uid = str(m.chat.id)
    bal = user_balances.get(uid, 0.0)
    bot.send_message(m.chat.id, f"Your wallet: ${bal:.2f}\n\nTo fund, contact admin.")

@bot.message_handler(commands=['add'])
def add_bal(m):
    if ADMIN_ID!= 0 and m.chat.id!= ADMIN_ID:
        return
    try:
        parts = m.text.split()
        target_id = parts[1]
        amount = float(parts[2])
        user_balances[target_id] = user_balances.get(target_id, 0.0) + amount
        save_balances(user_balances)
        bot.send_message(m.chat.id, f"Added ${amount} to {target_id}. New bal: ${user_balances[target_id]:.2f}")
        try:
            bot.send_message(int(target_id), f"✅ Admin don add ${amount} to your wallet!\nNew balance: ${user_balances[target_id]:.2f}")
        except:
            pass
    except Exception as e:
        bot.send_message(m.chat.id, f"Usage: /add USER_ID AMOUNT\nExample: /add 123456789 5\nError: {e}")

@bot.message_handler(commands=['cancel'])
def cancel_cmd(m):
    order_id = user_orders.get(m.chat.id)
    if not order_id:
        bot.send_message(m.chat.id, "No active order")
        return
    cancel_order(order_id)
    user_orders.pop(m.chat.id, None)
    bot.send_message(m.chat.id, f"Cancelled! Order {order_id} done.")

@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text.lower()
    uid = str(m.chat.id)

    if "my balance" in text:
        return mybal(m)
    if "cancel" in text:
        return cancel_cmd(m)

    if "usa" in text:
        country = "usa"
    elif "canada" in text:
        country = "canada"
    elif "argentina" in text:
        country = "argentina"
    elif "brazil" in text:
        country = "brazil"
    else:
        return

    price = PRICES.get(country, 2.0)
    bal = user_balances.get(uid, 0.0)

    if bal < price:
        bot.send_message(m.chat.id, f"❌ Insufficient balance!\nPrice: ${price}\nYour balance: ${bal:.2f}\n\nContact admin to fund wallet.")
        return

    bot.send_message(m.chat.id, f"Buying {country} number for ${price}...")

    try:
        data = buy_number(country)
        phone = data.get("phone")
        order_id = data.get("id")

        user_balances[uid] = bal - price
        save_balances(user_balances)
        user_orders[m.chat.id] = order_id

        bot.send_message(m.chat.id, f"✅ Number: {phone}\nOrder: {order_id}\nDeducted: ${price}\nRemaining: ${user_balances[uid]:.2f}\n\nWaiting for code...")

        for i in range(60):
            time.sleep(5)
            check = get_sms(order_id)
            sms = check.get("sms")
            if sms:
                user_orders.pop(m.chat.id, None)
                bot.send_message(m.chat.id, f"🔑 CODE: {sms}")
                return

        bot.send_message(m.chat.id, "No code yet. Send ❌ Cancel to cancel")

    except Exception as e:
        bot.send_message(m.chat.id, f"Error: {e}")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except:
            time.sleep(5)