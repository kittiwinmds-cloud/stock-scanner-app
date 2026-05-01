import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import requests

# =========================
# 🔔 DISCORD WEBHOOK
# =========================
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1499397129217769734/mvCVc6ArmwgHySBie_0seTHHFfQaW_I7v-R4HZG_vzlZRcgFu3dIGNKKVMos0Br5yinP"

def send_discord(symbol, signal, price):
    data = {
        "content": f"📊 SIGNAL ALERT\n{symbol} → {signal} @ {price:.2f}"
    }
    requests.post(DISCORD_WEBHOOK, json=data)


# =========================
# 🔥 STOCK LIST
# =========================
BASE_SYMBOLS = [
"NVDA","MSFT","AAPL","AMZN","GOOGL","META","PLTR",
"TSLA","AMD","SMCI","COIN","SNOW","CRWD",
"AVGO","MU","QCOM","INTC","MRVL","AMAT",
"JPM","BAC","GS","MS","WFC","C",
"XOM","CVX","OXY","SLB","COP",
"BA","LMT","RTX","CAT","GE",
"NKE","SBUX","MCD","WMT","COST","TGT",
"JNJ","PFE","LLY","ABBV","MRK",
"NFLX","DIS","CMCSA",
"O","PLD","AMT",
"SPY","QQQ","IWM","ARKK"
]

# =========================
# 🧠 STREAMLIT UI
# =========================
st.set_page_config(page_title="Stock Scanner", layout="wide")
st.title("📊 US Stock Scanner + Discord Alert")

run = st.button("🚀 Run Scan")

results = []
last_signal = {}


# =========================
# SCAN FUNCTION
# =========================
def scan(symbol):
    df = yf.download(symbol, interval="1h", period="60d", progress=False)

    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.dropna(inplace=True)

    df["ema_200"] = ta.trend.ema_indicator(df["Close"], window=200)
    df["bb_upper"] = ta.volatility.bollinger_hband(df["Close"])
    df["bb_lower"] = ta.volatility.bollinger_lband(df["Close"])
    df["vol_sma"] = df["Volume"].rolling(20).mean()

    df.dropna(inplace=True)

    if len(df) < 50:
        return None

    last = df.iloc[-2]

    high_volume = last["Volume"] > last["vol_sma"] * 1.2

    # =========================
    # LONG SIGNAL
    # =========================
    if last["Close"] > last["ema_200"] and last["Close"] > last["bb_upper"] and high_volume:

        if last_signal.get(symbol) != "LONG":
            send_discord(symbol, "LONG", last["Close"])
            last_signal[symbol] = "LONG"

        return (symbol, "LONG")

    # =========================
    # SHORT SIGNAL
    # =========================
    elif last["Close"] < last["ema_200"] and last["Close"] < last["bb_lower"] and high_volume:

        if last_signal.get(symbol) != "SHORT":
            send_discord(symbol, "SHORT", last["Close"])
            last_signal[symbol] = "SHORT"

        return (symbol, "SHORT")

    return None


# =========================
# RUN BUTTON
# =========================
if run:
    st.info("Scanning stocks...")

    progress = st.progress(0)

    for i, sym in enumerate(BASE_SYMBOLS):

        try:
            res = scan(sym)
            if res:
                results.append(res)

        except Exception as e:
            st.warning(f"{sym} error: {e}")

        progress.progress((i + 1) / len(BASE_SYMBOLS))

    st.success("Done!")

    # =========================
    # RESULT TABLE
    # =========================
    if results:
        df = pd.DataFrame(results, columns=["Symbol", "Signal"])

        st.subheader("🔥 Signals Found")
        st.dataframe(df, use_container_width=True)

        st.metric("Total Signals", len(df))

        st.write("### LONG")
        st.dataframe(df[df["Signal"] == "LONG"])

        st.write("### SHORT")
        st.dataframe(df[df["Signal"] == "SHORT"])

    else:
        st.warning("No signals found")