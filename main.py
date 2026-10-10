import os, requests, time
from threading import Thread
from flask import Flask
TOKEN=os.environ.get("BOT_TOKEN")
HERO_KEY=os.environ.get("HERO_KEY")
if HERO_KEY: HERO_KEY=HERO_KEY.strip()
API=f"https://api.telegram.org/bot{TOKEN}"
DOMAINS=["https://hero-sms.com/stubs/handler_api.php","https://www.hero-sms.com/stubs/handler_api.php"]
def send(cid,txt):
 try: requests.post(f"{API}/sendMessage",json={"chat_id":cid,"text":txt,"parse_mode":"HTML"},timeout=15)
 except: pass
def hero_call(a):
 last=""
 for d in DOMAINS:
  try:
   r=requests.get(f"{d}?api_key={HERO_KEY}&{a}",timeout=20)
   t=r.text.strip()
   if t and "<html" not in t.lower(): return t
   last=t[:150]
  except Exception as e: last=str(e)[:150]
 return f"Fail: {last}"
def bot_loop():
 offset=0; orders={}
 while True:
  try:
   res=requests.get(f"{API}/getUpdates?offset={offset}&timeout=30",timeout=35).json()
   for u in res.get("result",[]):
    offset=u["update_id"]+1
    if "message" not in u: continue
    cid=u["message"]["chat"]["id"]; txt=u["message"].get("text","").strip()
    if txt.startswith("/start"): send(cid,"<b>V6 LIVE</b>\n/balance\n/buy\n/code")
    elif "/balance" in txt: send(cid,f"<code>{hero_call('action=getBalance')}</code>")
    elif txt.startswith("/buy"):
     r=hero_call("action=getNumber&service=wa&country=19")
     if "ACCESS_NUMBER" in r:
      _,oid,num=r.split(":"); orders[cid]=oid; send(cid,f"Num <code>{num}</code> ID {oid} /code")
     else: send(cid,f"<code>{r}</code>")
    elif txt.startswith("/code"):
     oid=orders.get(cid)
     if not oid: send(cid,"No order")
     else:
      s=hero_call(f"action=getStatus&id={oid}")
      send(cid,f"<code>{s}</code>")
  except: time.sleep(2)
app=Flask(__name__)
@app.route("/")
def home(): return "OK"
Thread(target=bot_loop,daemon=True).start()
app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
