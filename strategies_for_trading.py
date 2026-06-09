# -*- coding: utf-8 -*-
"""Trading Strategies Backtester (Web Interface)"""

import datetime
import pandas as pd
import numpy as np
import vectorbt as vbt
import streamlit as st

st.set_page_config(layout="wide", page_title="Algorithmic Alpha Engine", page_icon="⚙️")

# --- Custom CCI Indicator ---
def cci_apply_func(high, low, close, window):
    high_s = pd.Series(high.squeeze())
    low_s = pd.Series(low.squeeze())
    close_s = pd.Series(close.squeeze())

    tp = (high_s + low_s + close_s) / 3
    sma = tp.rolling(window=window).mean()
    mad = tp.rolling(window=window).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    cci = (tp - sma) / (0.015 * mad)

    return cci.to_numpy()

CCI = vbt.IndicatorFactory(
    class_name="CCI",
    short_name="cci",
    input_names=["high", "low", "close"],
    param_names=["window"],
    output_names=["cci"]
).from_apply_func(cci_apply_func)

# --- UI ---
st.title("⚙️ Algorithmic Alpha Engine")
st.markdown("Automated equity trading backtester.")

st.sidebar.header("🛠️ Strategy Selection")
strategy = st.sidebar.selectbox(
    "Select Strategy",
    [
        "Dual Moving Average Crossover",
        "RSI Mean Reversion",
        "Bollinger Bands Breakout",
        "MACD Momentum",
        "CCI Breakout"
    ]
)

st.sidebar.header("📊 Global Parameters")
ticker = st.sidebar.text_input("Stock Ticker", "AAPL").strip().upper()
start_date = st.sidebar.date_input("Start Date", datetime.date(2020, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.date.today())
interval = st.sidebar.selectbox("Interval", ["1d", "1m", "5m", "1wk", "1mo"])
init_cash = st.sidebar.number_input("Initial Investment ($)", 100.0, value=10000.0)

st.sidebar.header("⚙️ Strategy Parameters")

if strategy == "Dual Moving Average Crossover":
    fast_ma_len = st.sidebar.number_input("Fast MA", 1, value=50)
    slow_ma_len = st.sidebar.number_input("Slow MA", 2, value=200)

elif strategy == "RSI Mean Reversion":
    rsi_window = st.sidebar.number_input("RSI Window", 2, value=14)
    rsi_lower = st.sidebar.number_input("RSI Lower", value=30.0)
    rsi_upper = st.sidebar.number_input("RSI Upper", value=70.0)

elif strategy == "Bollinger Bands Breakout":
    bb_window = st.sidebar.number_input("BB Window", 2, value=20)
    bb_std = st.sidebar.number_input("BB Std", value=2.0)

elif strategy == "MACD Momentum":
    fast_w = st.sidebar.number_input("MACD Fast", 1, value=12)
    slow_w = st.sidebar.number_input("MACD Slow", 2, value=26)
    signal_w = st.sidebar.number_input("MACD Signal", 1, value=9)

elif strategy == "CCI Breakout":
    cci_window = st.sidebar.number_input("CCI Window", 2, value=20)
    cci_upper = st.sidebar.number_input("CCI Upper", value=100.0)
    cci_lower = st.sidebar.number_input("CCI Lower", value=-100.0)

# --- RUN BACKTEST ---
if st.sidebar.button("🚀 Run Backtest", type="primary"):

    if not ticker:
        st.error("Please enter a ticker")
        st.stop()

    with st.spinner("Fetching data..."):
        yf_data = vbt.YFData.download(
            ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            interval=interval
        )

        close = yf_data.get("Close")
        high = yf_data.get("High")
        low = yf_data.get("Low")

        if close.empty:
            st.error("No data found")
            st.stop()

    with st.spinner("Running strategy..."):

        if strategy == "Dual Moving Average Crossover":
            fast = vbt.MA.run(close, fast_ma_len)
            slow = vbt.MA.run(close, slow_ma_len)
            entries = fast.ma_crossed_above(slow)
            exits = fast.ma_crossed_below(slow)

        elif strategy == "RSI Mean Reversion":
            rsi = vbt.RSI.run(close, window=rsi_window)
            entries = rsi.rsi_crossed_below(rsi_lower)
            exits = rsi.rsi_crossed_above(rsi_upper)

        elif strategy == "Bollinger Bands Breakout":
            bb = vbt.BBANDS.run(close, window=bb_window, alpha=bb_std)
            entries = bb.close_crossed_below(bb.lower)
            exits = bb.close_crossed_above(bb.upper)

        elif strategy == "MACD Momentum":
            macd = vbt.MACD.run(close, fast_window=fast_w, slow_window=slow_w, signal_window=signal_w)
            entries = macd.macd_crossed_above(macd.signal)
            exits = macd.macd_crossed_below(macd.signal)

        elif strategy == "CCI Breakout":
            cci = CCI.run(high, low, close, window=cci_window)
            entries = cci.cci_crossed_above(cci_upper)
            exits = cci.cci_crossed_below(cci_lower)

        portfolio = vbt.Portfolio.from_signals(
            close,
            entries,
            exits,
            init_cash=init_cash,
            freq="1D"
        )

    # --- RESULTS ---
    st.subheader(f"Results for {ticker}")

    stats = portfolio.stats()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Return %", f"{stats['Total Return [%]']:.2f}%")
    col2.metric("Win Rate %", f"{stats['Win Rate [%]']:.2f}%")
    col3.metric("Max Drawdown %", f"{stats['Max Drawdown [%]']:.2f}%")
    col4.metric("Final Value", f"${portfolio.value().iloc[-1]:,.2f}")

    st.markdown("### Performance")

    fig = portfolio.plot()
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Detailed Metrics")
    stats = portfolio.stats()

    # Convert Series → DataFrame
    stats_df = stats.to_frame(name="Value")

    # Make EVERYTHING Arrow-safe
    stats_df["Value"] = stats_df["Value"].apply(
        lambda x: str(x) if isinstance(x, (pd.Timedelta, object)) else x
    )

    st.dataframe(stats_df, use_container_width=True)