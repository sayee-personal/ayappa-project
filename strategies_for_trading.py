# -*- coding: utf-8 -*-
"""Trading Strategies Backtester (Web Interface)

A Streamlit web application providing five quantitative equity trading 
strategies built on vectorbt.

Strategies:
  1. Dual Moving Average Crossover
  2. RSI Mean Reversion
  3. Bollinger Bands Breakout
  4. MACD Momentum
  5. CCI Breakout (custom indicator)

Requirements:
  pip install vectorbt yfinance pandas numpy streamlit
"""

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


# --- UI Layout ---
st.title("⚙️ Algorithmic Alpha Engine")
st.markdown("Automated equity trading backtester. Simulate, validate, and deploy quantitative models.")

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
interval = st.sidebar.selectbox("Interval", ["1d", "1m", "2m", "5m", "15m", "30m", "60m", "90m", "5d", "1wk", "1mo"])
init_cash = st.sidebar.number_input("Initial Investment ($)", min_value=100.0, value=10000.0)

st.sidebar.header("⚙️ Strategy Parameters")

if strategy == "Dual Moving Average Crossover":
    fast_ma_len = st.sidebar.number_input("Fast MA Sessions", min_value=1, value=50)
    slow_ma_len = st.sidebar.number_input("Slow MA Sessions", min_value=2, value=200)

elif strategy == "RSI Mean Reversion":
    rsi_window = st.sidebar.number_input("RSI Lookback Period", min_value=2, value=14)
    rsi_lower = st.sidebar.number_input("RSI Lower (Oversold/Buy)", min_value=1.0, value=30.0)
    rsi_upper = st.sidebar.number_input("RSI Upper (Overbought/Sell)", min_value=1.0, value=70.0)

elif strategy == "Bollinger Bands Breakout":
    bb_window = st.sidebar.number_input("BB Period/Lookback", min_value=2, value=20)
    bb_std = st.sidebar.number_input("BB Standard Deviations", min_value=0.1, value=2.0)

elif strategy == "MACD Momentum":
    fast_w = st.sidebar.number_input("MACD Fast Period", min_value=1, value=12)
    slow_w = st.sidebar.number_input("MACD Slow Period", min_value=2, value=26)
    signal_w = st.sidebar.number_input("MACD Signal Period", min_value=1, value=9)

elif strategy == "CCI Breakout":
    cci_window = st.sidebar.number_input("CCI Lookback Period", min_value=2, value=20)
    cci_upper = st.sidebar.number_input("CCI Entry Threshold", value=100.0)
    cci_lower = st.sidebar.number_input("CCI Exit Threshold", value=-100.0)

# --- Execution Engine ---
if st.sidebar.button("🚀 Run Backtest", type="primary"):
    if not ticker:
        st.error("Please enter a valid ticker.")
        st.stop()

    st.markdown("---")
    
    with st.spinner(f"Fetching market data for {ticker}..."):
        try:
            yf_data = vbt.YFData.download(
                ticker, 
                start=start_date.strftime('%Y-%m-%d'), 
                end=end_date.strftime('%Y-%m-%d'), 
                interval=interval
            )
            close = yf_data.get("Close")
            high = yf_data.get("High")
            low = yf_data.get("Low")
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
            st.stop()

        if close.empty:
            st.warning("No data returned for the specified parameters.")
            st.stop()

    with st.spinner("Calculating signals and simulating portfolio..."):
        if strategy == "Dual Moving Average Crossover":
            fast_ma = vbt.MA.run(close, fast_ma_len)
            slow_ma = vbt.MA.run(close, slow_ma_len)
            entries = fast_ma.ma_crossed_above(slow_ma)
            exits = fast_ma.ma_crossed_below(slow_ma)
            
        elif strategy == "RSI Mean Reversion":
            rsi = vbt.RSI.run(close, window=rsi_window)
            entries = rsi.rsi_crossed_below(rsi_lower)
            exits = rsi.rsi_crossed_above(rsi_upper)
            
        elif strategy == "Bollinger Bands Breakout":
            bbands = vbt.BBANDS.run(close, window=bb_window, alpha=bb_std)
            entries = bbands.close_crossed_below(bbands.lower)
            exits = bbands.close_crossed_above(bbands.upper)
            
        elif strategy == "MACD Momentum":
            macd = vbt.MACD.run(close, fast_window=fast_w, slow_window=slow_w, signal_window=signal_w)
            entries = macd.macd_crossed_above(macd.signal)
            exits = macd.macd_crossed_below(macd.signal)
            
        elif strategy == "CCI Breakout":
            cci_ind = CCI.run(high, low, close, window=cci_window)
            entries = cci_ind.cci_crossed_above(cci_upper)
            exits = cci_ind.cci_crossed_below(cci_lower)

        portfolio = vbt.Portfolio.from_signals(close, entries, exits, init_cash=init_cash, freq="1D")

    # --- Render Results ---
    st.subheader(f"Results for {ticker} ({interval})")
    
    stats = portfolio.stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Return [%]", f"{stats['Total Return [%]']:.2f}%")
    with col2:
        st.metric("Win Rate [%]", f"{stats['Win Rate [%]']:.2f}%")
    with col3:
        st.metric("Max Drawdown [%]", f"{stats['Max Drawdown [%]']:.2f}%")
    with col4:
        st.metric("Final Value", f"${portfolio.value().iloc[-1]:,.2f}")
        
    st.markdown("### Performance Plot")
    fig = portfolio.plot()
    # Explicitly sizing to avoid Streamlit warning regressions
    st.plotly_chart(fig, width="stretch")

    st.markdown("### Detailed Metrics")
    st.dataframe(stats, width="stretch")
