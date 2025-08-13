"""
Plotly chart construction for the Streamlit stock watch app.

This module defines a function `build_chart` that assembles a multi‑row
Plotly Figure containing a candlestick chart with optional Bollinger
bands along with MACD and RSI subplots. Markers are added to
highlight buy/sell signal flips for each indicator.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .signals import State, macd_state, rsi_state, bb_state


def build_chart(
    df: pd.DataFrame,
    price_col: str,
    show_macd: bool,
    show_rsi: bool,
    show_bb: bool,
    theme_dark: bool = True,
    max_points: Optional[int] = None,
) -> go.Figure:
    """Construct a Plotly figure with price and indicator subplots.

    Args:
        df: DataFrame containing OHLC data and indicator columns.
        price_col: Name of the price column used for Bollinger evaluation.
        show_macd: Whether to display the MACD subplot.
        show_rsi: Whether to display the RSI subplot.
        show_bb: Whether to overlay Bollinger bands on the price chart.
        theme_dark: Whether to use a dark theme for the figure.
        max_points: Maximum number of points to display; older points are
            downsampled for performance. None means show all.

    Returns:
        A Plotly Figure ready for display in Streamlit.
    """
    # Optionally downsample long histories for performance. Indicators should
    # be computed on full resolution data; here we only reduce what gets
    # drawn. Keep the last max_points rows.
    if max_points is not None and len(df) > max_points:
        df_plot = df.iloc[-max_points:].copy()
    else:
        df_plot = df.copy()
    rows = 1
    row_heights = [0.6]
    if show_macd:
        rows += 1
        row_heights.append(0.2)
    if show_rsi:
        rows += 1
        row_heights.append(0.2)
    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=row_heights,
    )
    # Price candlestick
    fig.add_trace(
        go.Candlestick(
            x=df_plot.index,
            open=df_plot["Open"],
            high=df_plot["High"],
            low=df_plot["Low"],
            close=df_plot["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )
    # Bollinger bands overlay
    if show_bb:
        fig.add_trace(
            go.Scatter(x=df_plot.index, y=df_plot["BB_UPPER"], mode="lines", name="BB Upper"),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_plot.index, y=df_plot["BB_MID"], mode="lines", name="BB Middle"),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_plot.index, y=df_plot["BB_LOWER"], mode="lines", name="BB Lower"),
            row=1, col=1
        )
    # MACD subplot
    row_idx = 2 if show_macd else None
    if show_macd:
        # MACD line and signal line
        fig.add_trace(
            go.Scatter(x=df_plot.index, y=df_plot["MACD"], mode="lines", name="MACD"),
            row=row_idx, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_plot.index, y=df_plot["MACD_SIGNAL"], mode="lines", name="Signal"),
            row=row_idx, col=1
        )
        # Histogram
        fig.add_trace(
            go.Bar(x=df_plot.index, y=df_plot["MACD_HIST"], name="Histogram"),
            row=row_idx, col=1
        )
    # RSI subplot
    if show_rsi:
        rsi_row = rows if show_rsi and show_macd else (rows if show_rsi else None)
        # Actually compute row index: if both shown, MACD row is 2, RSI row is 3; if MACD hidden, RSI row is 2.
        if show_macd:
            rsi_row = 3 if show_rsi else None
        else:
            rsi_row = 2 if show_rsi else None
        fig.add_trace(
            go.Scatter(x=df_plot.index, y=df_plot["RSI"], mode="lines", name="RSI"),
            row=rsi_row, col=1
        )
        # Add overbought/oversold lines
        fig.add_trace(
            go.Scatter(x=df_plot.index, y=[70] * len(df_plot), mode="lines", name="RSI 70", line=dict(dash="dash")),
            row=rsi_row, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_plot.index, y=[50] * len(df_plot), mode="lines", name="RSI 50", line=dict(dash="dash")),
            row=rsi_row, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_plot.index, y=[30] * len(df_plot), mode="lines", name="RSI 30", line=dict(dash="dash")),
            row=rsi_row, col=1
        )
    # Add markers for indicator flips on price pane (only Bollinger)
    # Identify buy/sell events for each indicator
    marker_yoffset = (df_plot["Low"].min() * 0.99, df_plot["High"].max() * 1.01)
    # Precompute states on downsampled data
    macd_states = []
    rsi_states = []
    bb_states = []
    for i in range(len(df_plot)):
        macd_states.append(macd_state(df_plot, i))
        rsi_states.append(rsi_state(df_plot, i))
        bb_states.append(bb_state(df_plot, i, price_col))
    # Price pane markers for Bollinger signals
    buy_x = []
    buy_y = []
    sell_x = []
    sell_y = []
    for i, st in enumerate(bb_states):
        if st == State.BUY:
            buy_x.append(df_plot.index[i])
            buy_y.append(df_plot["Low"].iloc[i])
        elif st == State.SELL:
            sell_x.append(df_plot.index[i])
            sell_y.append(df_plot["High"].iloc[i])
    if buy_x:
        fig.add_trace(
            go.Scatter(
                x=buy_x,
                y=buy_y,
                mode="markers",
                name="BB Buy",
                marker=dict(symbol="triangle-up", size=8),
            ),
            row=1,
            col=1,
        )
    if sell_x:
        fig.add_trace(
            go.Scatter(
                x=sell_x,
                y=sell_y,
                mode="markers",
                name="BB Sell",
                marker=dict(symbol="triangle-down", size=8),
            ),
            row=1,
            col=1,
        )
    # Update layout for aesthetics
    fig.update_layout(
        showlegend=False,
        xaxis_rangeslider_visible=False,
        template="plotly_dark" if theme_dark else "plotly_white",
        margin=dict(l=40, r=20, t=40, b=40),
        hovermode="x unified",
    )
    # Set axes titles
    fig.update_yaxes(title_text="Price", row=1, col=1)
    yrow = 2
    if show_macd:
        fig.update_yaxes(title_text="MACD", row=yrow, col=1)
        yrow += 1
    if show_rsi:
        fig.update_yaxes(title_text="RSI", row=yrow, col=1)
    return fig
