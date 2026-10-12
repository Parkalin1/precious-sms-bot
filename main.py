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

def get_headers():
    key = os.getenv("SIM5_KEY", "").strip()
    return {
        "Authorization": f"Bearer {key}",
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

@app.route("/")
def home():
    return "Bot is Live"

@bot.message_handler(commands=['start'])
def start(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🇺🇸 USA", "🇨🇦 Canada", "🇦🇷 Argentina", "🇧🇷 Brazil")
    bot.send_message(m.chat.id, "Welcome! Choose country:", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text.lower()
    if "usa" in text:
        country = "usa"
    elif "canada" in text:
        country = "canada"
    elif "argentina" in text:
        country = "argentina"
    elif "brazil" in text:
        country = "brazil"
    else:
        country = "usa"

    bot.send_message(m.chat.id, f"Buying {country} number...")

    try:
        data = buy_number(country)
        phone = data.get("phone")
        order_id = data.get("id")
        bot.send_message(m.chat.id, f"Number: {phone}\nOrder ID: {order_id}\nWaiting for code...")

        for i in range(60):
            time.sleep(5)
            check = get_sms(order_id)
            sms = check.get("sms")
            if sms:
                bot.send_message(m.chat.id, f"CODE: {sms}")
                return

        bot.send_message(m.chat.id, "No code yet, try /start again")

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