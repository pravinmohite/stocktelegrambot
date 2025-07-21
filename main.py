import os, requests, yfinance as yf
import pandas as pd

BOT_TOKEN = '7745153783:AAHYmV0ZPdU6reeiwv3nrMO2fS_naQoJ10w'
CHAT_ID = '806642925'

from nsetools import Nse


def get_top_gainers():
    nse = Nse()
    try:
        top = nse.get_top_gainers()
        return [item["symbol"] + ".NS" for item in top[:10]]
    except Exception as e:
        print("Error using nsetools:", e)
        return []


def compute_rsi(data, window=14):
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi  # This is a Pandas Series


def analyze_stocks():
    picks = []
    for s in get_top_gainers():
        df = yf.download(s,
                         period="20d",
                         interval="1d",
                         progress=False,
                         auto_adjust=True)
        if df.empty:
            continue

        df["SMA5"] = df["Close"].rolling(5).mean()
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["RSI"] = compute_rsi(df)

        try:
            sma5 = df["SMA5"].iloc[-1]
            sma20 = df["SMA20"].iloc[-1]
            rsi = df["RSI"].iloc[-1]
        except Exception as e:
            print(f"Skipping {s} due to error:", e)
            continue

        # Check for NaN values before comparing
        if pd.notna(sma5) and pd.notna(sma20) and pd.notna(rsi):
            if sma5 > sma20 and rsi < 60:
                picks.append(s)
                print(f"✅ Bullish Signal: {s}")
                print(
                    f"Analyzing {s} | Latest RSI: {rsi:.2f}, SMA5: {sma5:.2f}, SMA20: {sma20:.2f}"
                )
            else:
                print(f"❌ No Signal for {s}")

    return picks


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    if response.status_code != 200:
        print("❌ Telegram Error:", response.text)



if __name__ == "__main__":
    picks = analyze_stocks()
    send_telegram("🔔 Dynamic bullish picks from today's gainers:\n" +
                  ("\n".join(picks) if picks else "⚠️ No signals found"))
