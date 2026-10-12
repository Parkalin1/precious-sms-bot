import threading

buying = {}  # add for top

@bot.message_handler(func=lambda m: m.text == "Portugal")
def buy_portugal(m):
    chat_id = m.chat.id
    if buying.get(chat_id):
        return
    buying[chat_id] = True
    msg = bot.send_message(chat_id, "Buying portugal... ⌛\n/cancel to stop")
    
    def run():
        # your 5sim buy code here
        # ...
        # after finish
        buying.pop(chat_id, None)

    threading.Thread(target=run).start()

@bot.message_handler(commands=['cancel'])
def do_cancel(m):
    buying.pop(m.chat.id, None)
    bot.send_message(m.chat.id, "✅ Cancelled! Click Europe Numbers again.")