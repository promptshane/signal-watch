"""
Generate buy/sell/hold signals from technical indicators.

This module defines a simple voting system based on MACD, RSI and
Bollinger Band states. Each indicator is reduced to a discrete state
(buy, sell or hold). A majority function determines an overall
recommendation. Additional helper functions expose the age (number
of bars since the last state change) and compute the latest
snapshot for a DataFrame.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

import pandas as pd


class State(str, Enum):
    """Discrete signal state for an indicator."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


def crossed_up(prev_a: float, curr_a: float, prev_b: float, curr_b: float) -> bool:
    """Return True if series a crossed up over series b at the current bar."""
    return (prev_a <= prev_b) and (curr_a > curr_b)


def crossed_down(prev_a: float, curr_a: float, prev_b: float, curr_b: float) -> bool:
    """Return True if series a crossed down below series b at the current bar."""
    return (prev_a >= prev_b) and (curr_a < curr_b)


def macd_state(df: pd.DataFrame, idx: int) -> State:
    """Determine the MACD state at a given index.

    Uses signal line crossover to generate buy and sell signals. If
    there is no crossover at the current bar, returns HOLD.

    Args:
        df: DataFrame containing columns 'MACD' and 'MACD_SIGNAL'.
        idx: Index of the row to evaluate.

    Returns:
        State.BUY, State.SELL or State.HOLD.
    """
    if idx <= 0:
        return State.HOLD
    p = idx - 1
    if crossed_up(df["MACD"].iloc[p], df["MACD"].iloc[idx], df["MACD_SIGNAL"].iloc[p], df["MACD_SIGNAL"].iloc[idx]):
        return State.BUY
    if crossed_down(df["MACD"].iloc[p], df["MACD"].iloc[idx], df["MACD_SIGNAL"].iloc[p], df["MACD_SIGNAL"].iloc[idx]):
        return State.SELL
    return State.HOLD


def rsi_state(df: pd.DataFrame, idx: int) -> State:
    """Determine the RSI state at a given index.

    RSI signals are generated when the RSI crosses key thresholds (30
    and 70 for strong signals, 50 for weaker momentum signals). For the
    MVP we treat all upward crossings as buy and downward crossings as
    sell, regardless of strength.

    Args:
        df: DataFrame containing a column 'RSI'.
        idx: Index of the row to evaluate.

    Returns:
        State.BUY, State.SELL or State.HOLD.
    """
    if idx <= 0:
        return State.HOLD
    p = idx - 1
    rsi_prev = df["RSI"].iloc[p]
    rsi_now = df["RSI"].iloc[idx]
    # Crosses up through 30 or 50 produce a buy state
    if crossed_up(rsi_prev, rsi_now, 30, 30) or crossed_up(rsi_prev, rsi_now, 50, 50):
        return State.BUY
    # Crosses down through 70 or 50 produce a sell state
    if crossed_down(rsi_prev, rsi_now, 70, 70) or crossed_down(rsi_prev, rsi_now, 50, 50):
        return State.SELL
    return State.HOLD


def bb_state(df: pd.DataFrame, idx: int, price_col: str) -> State:
    """Determine Bollinger Band state at a given index.

    Generates a buy state when the price closes below the lower band on
    the previous bar and closes back inside on the current bar. Sell
    signals occur for the opposite condition using the upper band.

    Args:
        df: DataFrame containing 'BB_UPPER' and 'BB_LOWER'.
        idx: Index of the row to evaluate.
        price_col: Name of the column containing the price series used
            when computing the Bollinger bands.

    Returns:
        State.BUY, State.SELL or State.HOLD.
    """
    if idx <= 0:
        return State.HOLD
    p = idx - 1
    c_prev = df[price_col].iloc[p]
    c_curr = df[price_col].iloc[idx]
    upper_prev = df["BB_UPPER"].iloc[p]
    lower_prev = df["BB_LOWER"].iloc[p]
    upper_curr = df["BB_UPPER"].iloc[idx]
    lower_curr = df["BB_LOWER"].iloc[idx]
    # Mean reversion buy: previous bar closed below the lower band and now back inside
    if c_prev < lower_prev and (lower_curr <= c_curr <= upper_curr):
        return State.BUY
    # Mean reversion sell: previous bar closed above the upper band and now back inside
    if c_prev > upper_prev and (lower_curr <= c_curr <= upper_curr):
        return State.SELL
    return State.HOLD


def signal_age(series_states: List[State], idx: int) -> int:
    """Compute how many bars ago the given state last changed.

    Args:
        series_states: List of states for each bar.
        idx: Index of the current bar.

    Returns:
        The number of bars since the last state change.
    """
    if idx < 0:
        return 0
    current = series_states[idx]
    age = 0
    for j in range(idx - 1, -1, -1):
        if series_states[j] != current:
            break
        age += 1
    return age


def majority(macd_s: State, rsi_s: State, bb_s: State) -> State:
    """Return the majority recommendation from three states.

    If two or more indicators agree on buy/sell the majority is returned,
    otherwise hold.
    """
    votes = [macd_s, rsi_s, bb_s]
    buys = sum(1 for v in votes if v == State.BUY)
    sells = sum(1 for v in votes if v == State.SELL)
    if buys >= 2:
        return State.BUY
    if sells >= 2:
        return State.SELL
    return State.HOLD


def latest_snapshot(df: pd.DataFrame, price_col: str) -> dict:
    """Compute the latest indicator snapshot for the most recent bar.

    Evaluates the MACD, RSI and Bollinger states at the last index and
    returns a dictionary summarising the results.

    Args:
        df: DataFrame with indicator columns.
        price_col: Column name to use for price in Bollinger evaluation.

    Returns:
        A dictionary with keys 'macd', 'rsi', 'bb', 'majority' and
        'index'.
    """
    if df.empty:
        raise ValueError("DataFrame is empty")
    idx = len(df) - 1
    macd_s = macd_state(df, idx)
    rsi_s = rsi_state(df, idx)
    bb_s = bb_state(df, idx, price_col)
    maj = majority(macd_s, rsi_s, bb_s)
    return {
        "macd": macd_s,
        "rsi": rsi_s,
        "bb": bb_s,
        "majority": maj,
        "index": df.index[idx],
    }
