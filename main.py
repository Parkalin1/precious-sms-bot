import os, requests, threading, time
from flask import Flask
import telebot

TOKEN = os.environ.get("BOT_TOKEN")
SIM5 = os.environ.get("SIM5_KEY")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
H = {"Authorization": f"Bearer {SIM5}"}
BASE = "https://5sim.net/v1"

buying = {}
orders = {}

@app.route('/')
def home():
    return "PRO 5SIM Bot is LIVE!"

@bot.message_handler(commands=['start'])
def start(m):
    buying.pop(m.chat.id, None)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🇪🇺 SELECT EUROPE:")
    markup.add("Portugal","Romania","Estonia")
    markup.add("Poland","Bulgaria","Netherlands")
    markup.add("💰 Balance")
    bot.send_message(m.chat.id, "Welcome PRO 5SIM Bot 🇪🇺\nEurope only!", reply_markup=markup)

@bot.message_handler(commands=['cancel'])
def cancel(m):
    buying.pop(m.chat.id, None)
    if m.chat.id in orders:
        try: requests.get(f"{BASE}/user/cancel/{orders[m.chat.id]}", headers=H, timeout=10)
        except: pass
        orders.pop(m.chat.id, None)
    bot.send_message(m.chat.id, "✅ Cancelled! Send /start")

@bot.message_handler(func=lambda m: True)
def handle(m):
    chat_id = m.chat.id
    txt = m.text.strip()

    if txt == "💰 Balance":
        try:
            r = requests.get(f"{BASE}/user/profile", headers=H, timeout=10).json()
            bot.send_message(chat_id, f"Balance: ${r.get('balance')}")
        except:
            bot.send_message(chat_id, "Error checking balance")
        return

    if txt in ["Portugal","Romania","Estonia","Poland","Bulgaria","Netherlands"]:
        if buying.get(chat_id):
            bot.send_message(chat_id, "Already buying... /cancel to stop")
            return
        buying[chat_id] = True
        bot.send_message(chat_id, f"Buying {txt.lower()}... ⌛\n/cancel to stop")

        def run():
            try:
                country = txt.lower()
                r = requests.get(f"{BASE}/user/buy/activation/country/{country}/operator/any/product/whatsapp", headers=H, timeout=20)
                if r.status_code!= 200:
                    bot.send_message(chat_id, f"❌ No {country} number. Try another.")
                    buying.pop(chat_id, None)
                    return
                data = r.json()
                orders[chat_id] = data['id']
                phone = data.get('phone')
                bot.send_message(chat_id, f"Number: {phone}\nWaiting for code... (2 mins)")

                for _ in range(6):
                    time.sleep(20)
                    if chat_id not in buying: return
                    try:
                        chk = requests.get(f"{BASE}/user/check/{data['id']}", headers=H, timeout=20).json()
                        if chk.get('sms'):
                            code = chk['sms'][0]['code']
                            bot.send_message(chat_id, f"✅ CODE: {code}\nNumber: {phone}")
                            buying.pop(chat_id, None)
                            orders.pop(chat_id, None)
                            return
                    except: continue

                # timeout - auto cancel
                try: requests.get(f"{BASE}/user/cancel/{data['id']}", headers=H, timeout=10)
                except: pass
                bot.send_message(chat_id, "❌ No code came. Auto-cancelled & refunded.")
                buying.pop(chat_id, None)
                orders.pop(chat_id, None)
            except Exception as e:
                buying.pop(chat_id, None)
                bot.send_message(chat_id, f"Error: {e}")

        threading.Thread(target=run).start()

# Run Flask + Bot
def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)