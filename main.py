import telebot, requests, time, os
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
SIM5_KEY = os.getenv("SIM5_KEY")
PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN)

PRICES = {
    "usa": 5000, "canada": 4500, "argentina": 3000, "brazil": 3000,
    "uk": 3500, "france": 3000, "germany": 3000, "italy": 3000,
    "spain": 3000, "netherlands": 3000, "sweden": 3000, "belgium": 3000
}

user_orders = {}
pending_pay = {}
user_wallets = {}

BASE = "https://5sim.net/v1"
def headers():
    return {"Authorization": f"Bearer {SIM5_KEY}", "Accept": "application/json"}

def buy_number(country):
    r = requests.get(f"{BASE}/user/buy/activation/{country}/any/whatsapp", headers=headers(), timeout=20)
    r.raise_for_status()
    return r.json()

def get_sms(order_id):
    r = requests.get(f"{BASE}/user/check/{order_id}", headers=headers(), timeout=15)
    r.raise_for_status()
    return r.json()

def cancel_order(order_id):
    try:
        requests.get(f"{BASE}/user/cancel/{order_id}", headers=headers(), timeout=15)
    except:
        pass

def init_paystack(email, amount, ref, country):
    url = "https://api.paystack.co/transaction/initialize"
    h = {"Authorization": f"Bearer {PAYSTACK_SECRET}", "Content-Type": "application/json"}
    data = {
        "email": email,
        "amount": int(amount * 100),
        "reference": ref,
        "metadata": {"country": country},
        "callback_url": "https://t.me/Precioussmsbot"
    }
    r = requests.post(url, headers=h, json=data, timeout=20)
    r.raise_for_status()
    return r.json()

def verify_paystack(ref):
    url = f"https://api.paystack.co/transaction/verify/{ref}"
    h = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    r = requests.get(url, headers=h, timeout=20)
    r.raise_for_status()
    return r.json()

@bot.message_handler(commands=['start'])
def start_cmd(m):
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    for c in PRICES:
        markup.add(types.KeyboardButton(c.upper()))
    markup.add(types.KeyboardButton("❌ Cancel"), types.KeyboardButton("💰 Wallet"))
    bot.send_message(m.chat.id, "Welcome to Precious SMS!\n\nAmerica + Europe countries available.\nChoose country, pay with Paystack, get code sharp!", reply_markup=markup)

@bot.message_handler(commands=['cancel'])
def cancel_cmd(m):
    pending_pay.clear()
    order_id = user_orders.get(m.chat.id)
    if not order_id:
        bot.send_message(m.chat.id, "Payment link cleared. Choose country again /start")
        return
    cancel_order(order_id)
    user_orders.pop(m.chat.id, None)
    bot.send_message(m.chat.id, "Cancelled!")

@bot.message_handler(commands=['mywallet', 'wallet'])
def wallet_cmd(m):
    bal = user_wallets.get(str(m.chat.id), 0)
    bot.send_message(m.chat.id, f"💰 Wallet: ₦{bal}\nIf number no dey after payment, money dey enter here.")

@bot.message_handler(func=lambda m: m.text and "wallet" in m.text.lower() and "💰" in m.text)
def wallet_btn(m):
    wallet_cmd(m)

@bot.message_handler(func=lambda m: True)
def all_handler(m):
    text = m.text.strip().lower() if m.text else ""
    if "cancel" in text and "❌" in m.text:
        cancel_cmd(m)
        return

    # If user sent email after choosing country
    if "@" in text and "." in text:
        # find last pending for this chat
        last_ref = None
        last_info = None
        for ref, info in pending_pay.items():
            if info['chat_id'] == m.chat.id and 'email' not in info:
                last_ref = ref
                last_info = info
                break
        if not last_info:
            for ref, info in list(pending_pay.items()):
                if info['chat_id'] == m.chat.id:
                    last_ref = ref
                    last_info = info
                    break

        if last_info and 'country' in last_info:
            email = m.text.strip()
            country = last_info['country']
            price = PRICES[country]
            ref = f"precious_{m.chat.id}_{int(time.time())}"
            try:
                pay = init_paystack(email, price, ref, country)
                if not pay.get("status"):
                    bot.send_message(m.chat.id, f"Paystack error: {pay}")
                    return
                link = pay["data"]["authorization_url"]
                pending_pay[ref] = {"chat_id": m.chat.id, "country": country, "price": price, "email": email}
                # remove old temp
                if last_ref in pending_pay and last_ref!= ref:
                    pending_pay.pop(last_ref, None)

                mk = types.InlineKeyboardMarkup()
                mk.add(types.InlineKeyboardButton("💳 Pay with Paystack", url=link))
                mk.add(types.InlineKeyboardButton("✅ I don pay - Verify", callback_data=f"verify_{ref}"))
                bot.send_message(m.chat.id, f"You choose {country.upper()} - ₦{price}\nEmail: {email}\n\nClick Pay with Paystack to pay, then click Verify after paying.", reply_markup=mk)
            except Exception as e:
                bot.send_message(m.chat.id, f"Paystack init failed: {e}")
            return

    # If user choose country
    if text in PRICES:
        if user_wallets.get(str(m.chat.id), 0) >= PRICES[text]:
            # use wallet
            try:
                data = buy_number(text)
                phone = data.get("phone")
                order_id = data.get("id")
                user_orders[m.chat.id] = order_id
                user_wallets[str(m.chat.id)] -= PRICES[text]
                bot.send_message(m.chat.id, f"✅ Using Wallet!\nNumber: {phone}\nOrder: {order_id}\nWaiting for code...")
            except Exception as e:
                err = str(e).lower()
                if "no" in err:
                    bot.send_message(m.chat.id, f"⚠️ {text.upper()} number no dey now. Your wallet still ₦{user_wallets.get(str(m.chat.id),0)}. Try another country.")
                else:
                    bot.send_message(m.chat.id, f"Buy failed: {e}")
            return

        # ask for email
        ref_temp = f"temp_{m.chat.id}_{int(time.time())}"
        pending_pay[ref_temp] = {"chat_id": m.chat.id, "country": text, "price": PRICES[text]}
        bot.send_message(m.chat.id, f"You choose {text.upper()} - ₦{PRICES[text]}\n\nSend your email address to generate Paystack payment link:")
        return

    bot.send_message(m.chat.id, "Choose country from keyboard or type /start")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data.startswith("verify_"):
        ref = call.data.split("verify_")[1]
        info = pending_pay.get(ref)
        if not info:
            bot.answer_callback_query(call.id, "Payment link expired, choose country again")
            return
        bot.send_message(call.message.chat.id, "⏳ Verifying payment...")
        try:
            v = verify_paystack(ref)
            if v.get("data") and v["data"].get("status") == "success":
                bot.send_message(call.message.chat.id, f"✅ Payment verified ₦{info['price']}! Buying {info['country'].upper()} number...")
                try:
                    data = buy_number(info['country'])
                    phone = data.get("phone")
                    order_id = data.get("id")
                    user_orders[call.message.chat.id] = order_id
                    bot.send_message(call.message.chat.id, f"✅ Number: {phone}\nOrder: {order_id}\nWaiting for WhatsApp code (60 tries)...")
                    pending_pay.pop(ref, None)
                    for i in range(60):
                        time.sleep(5)
                        check = get_sms(order_id)
                        sms = check.get("sms")
                        if sms:
                            bot.send_message(call.message.chat.id, f"🔑 CODE: {sms}\n\nUse am for WhatsApp!")
                            user_orders.pop(call.message.chat.id, None)
                            return
                    bot.send_message(call.message.chat.id, "No code yet. Send /cancel to cancel and refund to wallet")
                except Exception as e:
                    err = str(e).lower()
                    if "no" in err or "out of stock" in err or "not available" in err or "balance" in err:
                        uid = str(call.message.chat.id)
                        user_wallets[uid] = user_wallets.get(uid, 0) + info['price']
                        bot.send_message(call.message.chat.id, f"⚠️ {info['country'].upper()} number no dey for 5SIM now.\n\nNo worry! Your ₦{info['price']} don enter wallet.\nWallet: ₦{user_wallets[uid]}\nChoose another country, you no need pay again.")
                        pending_pay.pop(ref, None)
                    else:
                        bot.send_message(call.message.chat.id, f"Error after payment: {e}\nKeep Ref: {ref}, contact admin for refund.")
            else:
                bot.send_message(call.message.chat.id, "❌ Payment not complete yet. Pay finish for Paystack then click Verify again.")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"Verify failed: {e}")

print("Bot running...")
bot.infinity_polling()