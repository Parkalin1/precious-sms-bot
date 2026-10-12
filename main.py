import os
import time
import threading
import requests
import telebot
from telebot import types
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
SIM5_KEY = os.getenv("SIM5_KEY")
BASE = "https://5sim.net/v1"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
bot.remove_webhook()
time.sleep(1)

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Live!"

EUROPE = ["Portugal", "Romania", "Estonia", "Poland", "Bulgaria", "Netherlands"]
AMERICA = ["USA", "Canada", "Brazil", "Mexico", "Argentina", "Colombia", "Chile", "Peru"]

COUNTRY_MAP = {
    "portugal": "portugal",
    "romania": "romania",
    "estonia": "estonia",
    "poland": "poland",
    "bulgaria": "bulgaria",
    "netherlands": "netherlands",
    "usa": "usa",
    "canada": "canada",
    "brazil": "brazil",
    "mexico": "mexico",
    "argentina": "argentina",
    "colombia": "colombia",
    "chile": "chile",
    "peru": "peru"
}

H = {"Authorization": f"Bearer {SIM5_KEY}", "Accept": "application/json"}

buying = {}

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🇪🇺 Europe"), types.KeyboardButton("🌎 America"))
    markup.add(types.KeyboardButton("💰 Balance"))
    return markup

def europe_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add("Portugal", "Romania", "Estonia")
    markup.add("Poland", "Bulgaria", "Netherlands")
    markup.add("🔙 Back")
    return markup

def america_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add("USA", "Canada", "Brazil")
    markup.add("Mexico", "Argentina", "Colombia")
    markup.add("Chile", "Peru")
    markup.add("🔙 Back")
    return markup

def buy_number(chat_id, country_key, country_name):
    try:
        if not buying.get(chat_id):
            return
        bot.send_message(chat_id, f"Buying {country_name}... ⌛ /cancel to stop")

        r = requests.get(f"{BASE}/user/buy/activation/country/{country_key}/operator/any/product/whatsapp", headers=H, timeout=20)
        if r.status_code!= 200:
            r = requests.get(f"{BASE}/user/buy/activation/country/{country_key}/operator/any/product/any", headers=H, timeout=20)

        if not buying.get(chat_id):
            return

        if r.status_code == 200:
            data = r.json()
            bot.send_message(chat_id, f"✅ {country_name} number: `{data.get('phone')}`\nID: `{data.get('id')}`\n\nSend /code to get SMS", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, f"❌ No {country_name.lower()} number. Try another country or fund 5SIM.\nError: {r.text[:100]}")
    except Exception as e:
        bot.send_message(chat_id, f"Error: {e}")
    finally:
        buying.pop(chat_id, None)

@bot.message_handler(commands=['start'])
def start_cmd(m):
    buying.pop(m.chat.id, None)
    bot.send_message(m.chat.id, "Welcome PRO 5SIM Bot 🌍\nEurope + America Ready!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def all_text(m):
    txt = m.text.strip()
    chat_id = m.chat.id
    low = txt.lower()

    if low in ["/cancel", "cancel"]:
        buying.pop(chat_id, None)
        bot.send_message(chat_id, "✅ Cancelled.", reply_markup=main_menu())
        return

    if low in ["balance", "/balance", "💰 balance", "💲 balance"]:
        try:
            r = requests.get(f"{BASE}/user/profile", headers=H, timeout=10)
            bal = r.json().get('balance', '0') if r.status_code == 200 else 'Error'
            bot.send_message(chat_id, f"💰 Balance: ${bal}")
        except Exception as e:
            bot.send_message(chat_id, f"Error checking balance: {e}")
        return

    if txt in ["🇪🇺 Europe", "Europe", "europe"]:
        bot.send_message(chat_id, "Select Europe country:", reply_markup=europe_menu())
        return

    if txt in ["🌎 America", "America", "america"]:
        bot.send_message(chat_id, "Select America country:", reply_markup=america_menu())
        return

    if txt == "🔙 Back":
        buying.pop(chat_id, None)
        bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
        return

    if low in COUNTRY_MAP:
        if buying.get(chat_id):
            bot.send_message(chat_id, "Already buying... /cancel to stop")
            return
        buying[chat_id] = True
        threading.Thread(target=buy_number, args=(chat_id, COUNTRY_MAP[low], txt), daemon=True).start()
        return

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot polling started...")
    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)