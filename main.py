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
    "france": 4000,
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
    data = {
        "email": email,
        "amount": int(amount_naira * 100),
        "metadata": {"user_id": str(user_id), "country": country},
    }
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
    markup.add(
        "🇺🇸 USA ₦5000", "🇨🇦 Canada ₦4500",
        "🇦🇷 Argentina ₦2500", "🇧🇷 Brazil ₦2000",
        "🇬🇧 UK ₦5000", "🇩🇪 Germany ₦4500",
       