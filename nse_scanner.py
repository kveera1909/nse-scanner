import yfinance as yf
import pandas as pd
import time
import json
import requests
from threading import Thread
from flask import Flask, jsonify
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

# ================= TELEGRAM SETTINGS =================
TOKEN = "8408002627:AAH34dHw6CiF2fdI74Pp0JCF9OriEkesMnw"
CHAT_ID = "889983327"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot8408002627:AAH34dHw6CiF2fdI74Pp0JCF9OriEkesMnw/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ================= LOAD NSE STOCK LIST =================
print("Loading NSE stock list...")
url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
df = pd.read_csv(url)
stocks = [s + ".NS" for s in df["SYMBOL"]]
print("Total stocks:", len(stocks))

latest_signals = []

# ================= SCANNER FUNCTION =================
def scan_market():
    global latest_signals
    print("\nScanning market...")

    results = []

    for s in stocks[:800]:
        try:
            data = yf.download(s, interval="15m", period="2d", progress=False)

            if len(data) < 30:
                continue

            data["EMA20"] = EMAIndicator(data["Close"],20).ema_indicator()
            data["RSI"] = RSIIndicator(data["Close"],14).rsi()
            data["VOL_MA"] = data["Volume"].rolling(20).mean()

            last = data.iloc[-1]

            score = 0
            if last["Close"] > last["EMA20"]:
                score += 30
            if last["RSI"] > 65:
                score += 25
            if last["Volume"] > last["VOL_MA"]:
                score += 25
            if last["Close"] > data["High"].tail(10).max():
                score += 20

            if score >= 60:
                entry = float(last["Close"])
                stop = entry * 0.98
                target = entry * 1.04

                results.append({
                    "stock": s,
                    "entry": round(entry,2),
                    "stop": round(stop,2),
                    "target": round(target,2),
                    "score": score
                })

        except:
            pass

    results = sorted(results, key=lambda x: x["score"], reverse=True)
    latest_signals = results[:5]

    with open("signals.json","w") as f:
        json.dump(latest_signals, f)

    if latest_signals:
        msg = "🔥 TOP BREAKOUT STOCKS 🔥\n\n"
        for r in latest_signals:
            msg += (
                f"{r['stock']}\n"
                f"Entry: {r['entry']}\n"
                f"SL: {r['stop']}\n"
                f"Target: {r['target']}\n"
                f"Score: {r['score']}\n\n"
            )
    else:
        msg = "No breakout stocks now"

    print(msg)
    send_telegram(msg)

# ================= LOOP =================
def scanner_loop():
    while True:
        scan_market()
        print("Waiting 5 minutes...\n")
        time.sleep(300)

# ================= API =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Scanner running"

@app.route("/signals")
def signals():
    return jsonify(latest_signals)

# ================= START =================
if __name__ == "__main__":
    Thread(target=scanner_loop).start()
    app.run(host="0.0.0.0", port=8080)
