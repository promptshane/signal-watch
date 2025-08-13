"""
Data fetching and caching functions for the Streamlit app.

This module wraps the free Yahoo Finance API (via yfinance) and
predefines a set of common timeframes. It exposes a single `fetch`
function that returns a DataFrame and the name of the price column used
for indicator computations. Results are cached by Streamlit based on
time to live (TTL) depending on whether data are intraday or daily.
"""

from __future__ import annotations

from datetime import datetime
from typing import Tuple

import pandas as pd
import streamlit as st
import yfinance as yf

# Define timeframe configurations used in the UI.  Each entry maps to a
# dict describing the `period` and `interval` parameters for
# yfinance.download, plus a flag indicating whether the data are
# intraday (which implies a shorter caching TTL and slightly different
# price column handling).
TF = {
    "1D": {"period": "1d", "interval": "1m", "intraday": True},
    "1W": {"period": "7d", "interval": "15m", "intraday": True},
    "1M": {"period": "1mo", "interval": "1d", "intraday": False},
    "3M": {"period": "3mo", "interval": "1d", "intraday": False},
    "6M": {"period": "6mo", "interval": "1d", "intraday": False},
    "1Y": {"period": "1y", "interval": "1d", "intraday": False},
    "5Y": {"period": "5y", "interval": "1wk", "intraday": False},
    "Max": {"period": "max", "interval": "1mo", "intraday": False},
}


@st.cache_data(show_spinner=False)
def fetch(symbol: str, tf_key: str) -> Tuple[pd.DataFrame, str]:
    """Fetch market data for a symbol and timeframe.

    Uses yfinance to download free historical data from Yahoo. Caches
    results via Streamlit's caching to reduce repeated API calls. If the
    download fails or returns an empty DataFrame, a ValueError is
    raised.

    Args:
        symbol: Ticker symbol to fetch.
        tf_key: Key into the TF mapping selecting period and interval.

    Returns:
        A tuple of (DataFrame, price_column_name). The DataFrame
        contains columns renamed to title case (Open, High, Low, Close,
        Adj Close, Volume) and an additional 'PriceCol' column pointing
        to the price column to use for indicators.
    """
    cfg = TF.get(tf_key)
    if cfg is None:
        raise KeyError(f"Unknown timeframe: {tf_key}")
    # Download the data; disable progress bar
    df = yf.download(symbol, period=cfg["period"], interval=cfg["interval"], progress=False, auto_adjust=False)
    if df is None or df.empty:
        raise ValueError("No data returned. Try a different timeframe or symbol.")
    # Normalise column names to title case (e.g. 'Close')
    df = df.rename(columns=str.title)
    # Use Adjusted Close for daily/weekly intervals, raw Close for intraday
    price_col = "Close" if cfg["intraday"] else "Adj Close"
    # Drop last partial intraday bar
    if cfg["intraday"] and len(df) > 1:
        df = df.iloc[:-1]
    # Provide a unified column for price references
    df["PriceCol"] = df[price_col]
    return df, price_col
