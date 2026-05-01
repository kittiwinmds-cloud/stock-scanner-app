import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# =========================
# CONFIG
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
# UI
# =========================
st.set_page_config(page_title="US Stock Scanner", layout="wide")

st.title("📊 US Stock Scanner (EMA + BB + Volume)")

col1, col2 = st.columns(2)
run = col1.button("🚀 Run Scan")
limit = col2.slider("Max symbols", 5, len(BASE_SYMBOLS), 20)

results = []

# =========================
# SCAN FUNCTION
# =========================
def scan_symbol(symbol):
    df = yf.download(symbol, interval="1h", period="60d", progress=False)

    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.dropna(inplace=True)

    # Indicators
    df["ema_200"] = ta.trend.ema_indicator(df["Close"], window=200)
    df["bb_upper"] = ta.volatility.bollinger_hband(df["Close"])
    df["bb_lower"] = ta.volatility.bollinger_lband(df["Close"])
    df["vol_sma"] = df["Volume"].rolling(20).mean()

    df.dropna(inplace=True)

    if len(df) < 50:
        return None

    last = df.iloc[-2]

    high_volume = last["Volume"] > last["vol_sma"] * 1.2

    if last["Close"] > last["ema_200"] and last["Close"] > last["bb_upper"] and high_volume:
        return (symbol, "LONG")

    elif last["Close"] < last["ema_200"] and last["Close"] < last["bb_lower"] and high_volume:
        return (symbol, "SHORT")

    return None


# =========================
# RUN
# =========================
if run:
    st.info("Scanning... please wait ⏳")

    progress = st.progress(0)

    for i, symbol in enumerate(BASE_SYMBOLS[:limit]):
        res = scan_symbol(symbol)
        if res:
            results.append(res)

        progress.progress((i + 1) / limit)

    st.success("Scan completed!")

    # =========================
    # RESULT
    # =========================
    if results:
        df_result = pd.DataFrame(results, columns=["Symbol", "Signal"])

        st.subheader("🔥 Signals Found")

        st.dataframe(df_result, use_container_width=True)

        # summary
        st.metric("Total Signals", len(df_result))

        st.write("### LONG")
        st.dataframe(df_result[df_result["Signal"] == "LONG"])

        st.write("### SHORT")
        st.dataframe(df_result[df_result["Signal"] == "SHORT"])

    else:
        st.warning("No setup found ❌")