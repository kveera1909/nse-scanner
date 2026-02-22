import yfinance as yf
import pandas as pd
import time
import requests
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

# ===== TELEGRAM SETTINGS =====
TOKEN = "8408002627:AAHshwFfdinh1XFlqjWADOxI_P6_vfyE4KY"
CHAT_ID = "889983327"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

print("Loading NSE stock list...")

# ===== LOAD NSE STOCK LIST =====
url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
df = pd.read_csv(url)
stocks = [s + ".NS" for s in df["SYMBOL"]]

print("Total stocks:", len(stocks))

# ===== SCANNER FUNCTION =====
def scan_market():
    print("\nScanning market...")
    results = []

    for s in stocks[:800]:   # increase later if needed
        try:
            data = yf.download(s, interval="15m", period="2d", progress=False)

            if len(data) < 30:
                continue

            data["EMA20"] = EMAIndicator(data["Close"],20).ema_indicator()
            data["RSI"] = RSIIndicator(data["Close"],14).rsi()
            data["VOL_MA"] = data["Volume"].rolling(20).mean()

            last = data.iloc[-1]

            # ===== PROBABILITY SCORE =====
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
                entry = last["Close"]
                stop = entry * 0.98
                target = entry * 1.04

                results.append({
                    "stock": s,
                    "entry": entry,
                    "stop": stop,
                    "target": target,
                    "score": score
                })

        except:
            pass

    # ===== SORT STRONGEST FIRST =====
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    # ===== OUTPUT =====
    if results:
        msg = "🔥 TOP BREAKOUT STOCKS 🔥\n\n"

        for r in results[:5]:
            msg += (
                f"{r['stock']}\n"
                f"Entry: {r['entry']:.2f}\n"
                f"SL: {r['stop']:.2f}\n"
                f"Target: {r['target']:.2f}\n"
                f"Score: {r['score']}\n\n"
            )

        print(msg)
        send_telegram(msg)

    else:
        msg = "No breakout stocks now"
        print(msg)
        send_telegram(msg)

# ===== AUTO RUN EVERY 5 MINUTES =====
while True:
    scan_market()
    print("Waiting 5 minutes for next scan...\n")
    time.sleep(300)