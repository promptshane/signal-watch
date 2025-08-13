"""
Technical indicator calculations used by the Streamlit stock watch app.

This module implements a handful of common indicators including EMA,
MACD, RSI and Bollinger Bands. The functions operate on pandas Series
objects and return Series aligned to the input index.  A helper
`attach_indicators` function computes all supported indicators and
appends them to the passed DataFrame.

No third‑party TA library is used; everything is implemented with
vectorised pandas operations so that the project has no extra
dependencies beyond pandas and numpy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    """Compute an exponential moving average (EMA).

    Args:
        series: Price series.
        span: Length of the exponential window.

    Returns:
        A new Series containing the EMA.
    """
    return series.ewm(span=span, adjust=False).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD line, signal line and histogram.

    The MACD line is the difference between two EMAs. The signal line
    is an EMA of the MACD line itself, and the histogram is the
    difference between the two. Defaults correspond to the common
    (12,26,9) configuration.

    Args:
        close: Closing price series.
        fast: Fast EMA span.
        slow: Slow EMA span.
        signal: Signal line EMA span.

    Returns:
        A tuple of (macd_line, signal_line, histogram) series.
    """
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Compute the Relative Strength Index (RSI).

    Uses Wilder's smoothing algorithm for averaging gains and losses.

    Args:
        close: Closing price series.
        period: Lookback period for computing average gain/loss.

    Returns:
        An RSI series scaled from 0–100.
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Simple moving average of gains/losses for the first period
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    # Wilder's exponential smoothing for subsequent values
    avg_gain = avg_gain.shift(1).ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = avg_loss.shift(1).ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    return rsi_series


def bollinger(close: pd.Series, n: int = 20, n_std: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Compute Bollinger Bands.

    The middle band is an n‑period simple moving average. Upper and
    lower bands are n_std standard deviations above and below the
    moving average, respectively.

    Args:
        close: Closing price series.
        n: Length of the moving average window.
        n_std: Number of standard deviations for the bands.

    Returns:
        A tuple of (upper, middle, lower) bands.
    """
    mid = close.rolling(n).mean()
    std = close.rolling(n).std(ddof=0)
    upper = mid + n_std * std
    lower = mid - n_std * std
    return upper, mid, lower


def attach_indicators(df: pd.DataFrame, price_col: str) -> pd.DataFrame:
    """Attach computed indicators to a DataFrame in place.

    This function adds MACD (line, signal and histogram), RSI and
    Bollinger Bands to the given DataFrame. Columns will be named
    ``MACD``, ``MACD_SIGNAL``, ``MACD_HIST``, ``RSI``, ``BB_UPPER``,
    ``BB_MID`` and ``BB_LOWER``. The passed DataFrame is mutated and
    returned for convenience.

    Args:
        df: DataFrame with a price column.
        price_col: Column name to use for closing price.

    Returns:
        The same DataFrame with indicator columns appended.
    """
    close = df[price_col]
    macd_line, macd_signal, macd_hist = macd(close)
    df["MACD"] = macd_line
    df["MACD_SIGNAL"] = macd_signal
    df["MACD_HIST"] = macd_hist
    df["RSI"] = rsi(close)
    bb_upper, bb_mid, bb_lower = bollinger(close)
    df["BB_UPPER"] = bb_upper
    df["BB_MID"] = bb_mid
    df["BB_LOWER"] = bb_lower
    return df
