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
        df = yf.download(s, period="25d", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 20:
            continue

        df["SMA5"] = df["Close"].rolling(5).mean()
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["RSI"] = compute_rsi(df)
        df["AvgVol10"] = df["Volume"].rolling(10).mean()

        try:
            sma5 = df["SMA5"].iloc[-1]
            sma5_prev = df["SMA5"].iloc[-2]
            sma20 = df["SMA20"].iloc[-1]
            sma20_prev = df["SMA20"].iloc[-2]
            rsi = df["RSI"].iloc[-1]
            today_vol = df["Volume"].iloc[-1]
            avg_vol = df["AvgVol10"].iloc[-2]  # yesterday’s avg
            recent_high = df["Close"].iloc[-10:].max()
            close = df["Close"].iloc[-1]
        except Exception as e:
            print(f"Skipping {s} due to error:", e)
            continue

        # Apply improved conditions
        if (
            pd.notna(sma5) and pd.notna(sma20) and pd.notna(rsi)
            and sma5 > sma20
            and sma5_prev < sma20_prev  # Fresh crossover
            and 45 <= rsi <= 60
            and today_vol > 1.5 * avg_vol  # Volume surge
            and close >= recent_high * 0.98  # near breakout
        ):
            picks.append(f"{s} (RSI: {rsi:.2f}, SMA5: {sma5:.2f}, SMA20: {sma20:.2f})")
            print(f"✅ Bullish Signal: {s}")
            print(
                f"RSI: {rsi:.2f}, SMA5: {sma5:.2f}, SMA20: {sma20:.2f}, Vol: {today_vol}, AvgVol: {avg_vol:.0f}, Close: {close}, 10d High: {recent_high}"
            )
        else:
            print(f"❌ No Signal for {s}")

    return picks


# def analyze_stocks():
#     picks = []
#     messages = []

#     for s in get_top_gainers():
#         df = yf.download(s,
#                          period="20d",
#                          interval="1d",
#                          progress=False,
#                          auto_adjust=True)
#         if df.empty:
#             continue

#         df["SMA5"] = df["Close"].rolling(5).mean()
#         df["SMA20"] = df["Close"].rolling(20).mean()
#         df["RSI"] = compute_rsi(df)

#         try:
#             sma5 = df["SMA5"].iloc[-1]
#             sma20 = df["SMA20"].iloc[-1]
#             rsi = df["RSI"].iloc[-1]
#             open_price = df["Open"].iloc[-1]
#             close_price = df["Close"].iloc[-1]
#         except Exception as e:
#             print(f"Skipping {s} due to error:", e)
#             continue

#         if pd.notna(sma5) and pd.notna(sma20) and pd.notna(rsi):
#             if sma5 > sma20 and rsi < 60:
#                 today_change = ((close_price - open_price) / open_price) * 100
#                 potential_target = sma5 + (sma5 - sma20)
#                 potential_gain = ((potential_target - close_price) / close_price) * 100

#                 msg_line = (
#                     f"✅ {s} | ▲ {today_change:.2f}% today | RSI: {rsi:.1f} | "
#                     f"SMA5: {sma5:.1f} > SMA20: {sma20:.1f} | Est. Gain: +{potential_gain:.1f}%"
#                 )

#                 print(msg_line)
#                 picks.append(s)
#                 messages.append(msg_line)
#             else:
#                 print(f"❌ No Signal for {s}")

#     if not messages:
#         messages.append("⚠️ No bullish signals found today.")

#     return messages


# def analyze_stocks():
#     picks = []
#     for s in get_top_gainers():
#         df = yf.download(s,
#                          period="20d",
#                          interval="1d",
#                          progress=False,
#                          auto_adjust=True)
#         if df.empty:
#             continue

#         df["SMA5"] = df["Close"].rolling(5).mean()
#         df["SMA20"] = df["Close"].rolling(20).mean()
#         df["RSI"] = compute_rsi(df)

#         try:
#             sma5 = df["SMA5"].iloc[-1]
#             sma20 = df["SMA20"].iloc[-1]
#             rsi = df["RSI"].iloc[-1]
#         except Exception as e:
#             print(f"Skipping {s} due to error:", e)
#             continue

#         # Check for NaN values before comparing
#         if pd.notna(sma5) and pd.notna(sma20) and pd.notna(rsi):
#             if sma5 > sma20 and rsi < 60:
#                 picks.append(s)
#                 print(f"✅ Bullish Signal: {s}")
#                 print(
#                     f"Analyzing {s} | Latest RSI: {rsi:.2f}, SMA5: {sma5:.2f}, SMA20: {sma20:.2f}"
#                 )
#             else:
#                 print(f"❌ No Signal for {s}")

#     return picks


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    if response.status_code != 200:
        print("❌ Telegram Error:", response.text)



if __name__ == "__main__":
    picks = analyze_stocks()
    send_telegram("🔔 Dynamic bullish picks from today's gainers:\n" +
                  ("\n".join(picks) if picks else "⚠️ No signals found"))
