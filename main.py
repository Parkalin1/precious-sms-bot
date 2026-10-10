import os, requests, time
from threading import Thread
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
SIM5 = (os.environ.get("5SIM_KEY") or os.environ.get("SMS_KEY") or "").strip()
API = f"https://api.telegram.org/bot{TOKEN}"
BASE = "https://5sim.net/v1"
HEADERS = {"Authorization": f"Bearer {SIM5}", "Accept": "application/json"}

COUNTRIES = {
    "usa": "USA 🇺🇸",
    "england": "UK 🇬🇧",
    "poland": "Poland 🇵🇱 Cheap",
    "canada": "Canada 🇨🇦",
    "germany": "Germany 🇩🇪",
    "brazil": "Brazil 🇧🇷",
    "india": "India 🇮🇳",
    "nigeria": "Nigeria 🇳🇬",
    "philippines": "Philippines 🇵🇭",
    "southafrica": "South Africa 🇿🇦"
}

def send(cid, txt):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": cid, "text": txt, "parse_mode": "HTML"}, timeout=15)
    except: pass

def bot_loop():
    print("V12 5SIM STARTED")
    offset=0
    orders={}
    while True:
        try:
            res=requests.get(f"{API}/getUpdates?offset={offset}&timeout=30", timeout=35).json()
            for u in res.get("result",[]):
                offset=u["update_id"]+1
                if "message" not in u: continue
                cid=u["message"]["chat"]["id"]
                txt=u["message"].get("text","").strip().lower()

                if txt.startswith("/start"):
                    send(cid,"<b>V12 5SIM BOT LIVE ✅</b>\n\n/countries\n/balance\n/buy whatsapp usa\n/buy whatsapp poland\n/buy telegram england\n/code\n/cancel")

                elif "countries" in txt:
                    msg="<b>Countries:</b>\n"
                    for k,v in COUNTRIES.items():
                        msg+=f"{k} - {v}\n"
                    msg+="\nEx: /buy whatsapp usa"
                    send(cid,msg)

                elif "/balance" in txt:
                    try:
                        r=requests.get(f"{BASE}/user/profile", headers=HEADERS, timeout=15).json()
                        send(cid,f"Balance: ${r.get('balance')} | Rating: {r.get('rating')}")
                    except Exception as e:
                        send(cid,f"Balance error: {e} - check 5SIM_KEY")

                elif txt.startswith("/buy"):
                    p=txt.split()
                    product=p[1] if len(p)>1 else "whatsapp"
                    country=p[2] if len(p)>2 else "usa"
                    if product=="wa": product="whatsapp"
                    if product=="tg": product="telegram"
                    send(cid,f"Buying {product} {country}...")
                    try:
                        url=f"{BASE}/user/buy/activation/{country}/any/{product}"
                        r=requests.get(url, headers=HEADERS, timeout=20).json()
                        print(r)
                        if "id" in r and "phone" in r:
                            orders[cid]=r["id"]
                            send(cid,f"✅ {country}\nNumber: <code>{r['phone']}</code>\nID: <code>{r['id']
