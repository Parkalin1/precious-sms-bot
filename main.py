import os
import time
import threading
import requests
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SIM5_KEY = os.getenv("SIM5_KEY", "").strip()

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

BASE = "https://5sim.net/v1"
user_orders = {}

def get_headers():
    return {
        "Authorization": f"Bearer {os.getenv('SIM5_KEY','').strip()}",
        "Accept": "application/json"
    }

def buy_number(country):
    url = f"{BASE}/user/buy/activation/{country}/any/whatsapp"
    r = requests.get(url, headers=get_headers(), timeout=30)
    print(f"5SIM raw: {r.text[:500]}")
    if r.status_code != 200:
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

def get_balance():
    url = f"{BASE}/user/profile"
    r = requests.get(url, headers=get_headers(), timeout=20)
    if r.status_code == 200:
        try:
            return r.json().get("balance")
        except:
            return None
    return None

@app.route("/")
def home():
    return "Bot is Live"

@bot.message_handler(commands=['start'])
def start(m):
    bal = get_balance()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🇺🇸 USA", "🇨🇦 Canada", "🇦🇷 Argentina", "🇧🇷 Brazil")
    markup.add("💰 Balance", "❌ Cancel")
    txt = f"Welcome! Balance: ${bal}\nChoose country:" if bal is not None else "Welcome! Choose country:"
    bot.send_message(m.chat.id, txt, reply_markup=markup)

@bot.message_handler(commands=['cancel'])
def cancel_cmd(m):
    order_id = user_orders.get(m.chat.id)
    if not order_id:
        bot.send_message(m.chat.id, "No active order to cancel")
        return
    res = cancel_order(order_id)
    user_orders.pop(m.chat.id, None)
    bot.send_message(m.chat.id, f"Cancelled order {order_id}\n{res[:200]}")

@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text.lower()

    if "balance" in text:
        bal = get_balance()
        bot.send_message(m.chat.id, f"Your 5SIM Balance: ${bal}")
        return

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

    bot.send_message(m.chat.id, f"Buying {country} number...")

    try:
        data = buy_number(country)
        phone = data.get("phone")
        order_id = data.get("id")
        user_orders[m.chat.id] = order_id
        bot.send_message(m.chat.id, f"Number: {phone}\nOrder ID: {order_id}\nWaiting for code...\nSend ❌ Cancel if you want to cancel")

        for i in range(60):
            time.sleep(5)
            check = get_sms(order_id)
            sms = check.get("sms")
            if sms:
                user_orders.pop(m.chat.id, None)
                bot.send_message(m.chat.id, f"CODE: {sms}")
                return

        bot.send_message(m.chat.id, "No code yet. Send /cancel to cancel and get refund")

    except Exception as e:
        bot.send_message(m.chat.id, f"Error: {e}")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot polling started...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Polling error: {e}, retrying in 5s...")
            time.sleep(5)