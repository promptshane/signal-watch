"""
Main entrypoint for the Streamlit stock signal watch application.

This module orchestrates data fetching, indicator computation and UI
rendering. It allows users to search for tickers, build a watchlist
and view charts with optional technical indicators. A simple voting
mechanism summarises signals from MACD, RSI and Bollinger Bands.

To run the app locally, install dependencies listed in requirements.txt
and execute:

    streamlit run signal_watch/app.py

"""

from __future__ import annotations

import json
from typing import List, Dict, Any

import pandas as pd
import streamlit as st

from . import data
from . import indicators
from . import signals
from . import charts
from . import search
from . import storage


@st.cache_data(show_spinner=False, ttl=60)
def compute_snapshot(symbol: str, tf_key: str) -> Dict[str, Any]:
    """Compute the latest signal snapshot for a symbol/timeframe.

    This helper wraps fetching, indicator attachment and snapshot
    calculation behind a cache for performance. The TTL is short to
    allow intraday updates. If fetching or computation fails, the
    error is propagated.
    """
    df, price_col = data.fetch(symbol, tf_key)
    df = indicators.attach_indicators(df, price_col)
    snap = signals.latest_snapshot(df, price_col)
    last_price = df[price_col].iloc[-1]
    return {
        "symbol": symbol,
        "price": float(last_price),
        "macd": snap["macd"],
        "rsi": snap["rsi"],
        "bb": snap["bb"],
        "majority": snap["majority"],
        "time": str(snap["index"]),
    }


def state_dot(state: signals.State) -> str:
    """Render a coloured dot emoji for a given state."""
    return {signals.State.BUY: "🟢", signals.State.SELL: "🔴", signals.State.HOLD: "🟡"}[state]


def display_watchlist_overview(tf_key: str, show_macd: bool, show_rsi: bool, show_bb: bool) -> None:
    """Render the watchlist overview table.

    Iterates over the current watchlist, computes snapshots and displays
    them in a table with colour coded indicator states. Rows include
    buttons to open the detail view for each symbol.
    """
    watchlist = st.session_state.get("watchlist", [])
    if not watchlist:
        st.info("Your watchlist is empty. Add a ticker using the sidebar to get started.")
        return
    rows = []
    errors = {}
    for sym in watchlist:
        try:
            snap = compute_snapshot(sym, tf_key)
            rows.append(snap)
        except Exception as e:
            errors[sym] = str(e)
    if rows:
        # Build DataFrame for display
        df_rows = []
        for row in rows:
            df_rows.append({
                "Ticker": row["symbol"],
                "Price": row["price"],
                "MACD": state_dot(row["macd"]),
                "RSI": state_dot(row["rsi"]),
                "BB": state_dot(row["bb"]),
                "Majority": row["majority"].value,
                "Time": row["time"],
            })
        df_display = pd.DataFrame(df_rows)
        # Sort by majority (BUY first) and number of buy dots
        def buy_count(r):
            return (1 if r["MACD"] == "🟢" else 0) + (1 if r["RSI"] == "🟢" else 0) + (1 if r["BB"] == "🟢" else 0)
        df_display.sort_values(by=["Majority", "Ticker"], ascending=[True, True], inplace=True)
        st.dataframe(df_display, hide_index=True)
    if errors:
        for sym, err in errors.items():
            st.warning(f"{sym}: {err}")


def run() -> None:
    """Main application function."""
    st.set_page_config(page_title="Signal Watch", layout="wide")
    storage.init_watchlist()
    st.sidebar.title("Signal Watch")
    st.sidebar.caption("Free data via Yahoo • Educational only")
    # Timeframe selection
    tf_key = st.sidebar.radio("Timeframe", list(data.TF.keys()), index=2, horizontal=False)
    # Indicator toggles
    show_bb = st.sidebar.checkbox("Bollinger Bands", value=True)
    show_macd = st.sidebar.checkbox("MACD", value=True)
    show_rsi = st.sidebar.checkbox("RSI", value=True)
    theme_dark = st.sidebar.toggle("Dark mode", value=True)
    # Watchlist manager
    st.sidebar.subheader("Watchlist")
    sym_in = st.sidebar.text_input("Add symbol", key="add_symbol")
    if st.sidebar.button("Add", key="add_button"):
        if sym_in:
            storage.add_to_watchlist(sym_in.strip().upper())
            st.sidebar.success(f"Added {sym_in.strip().upper()} to watchlist.")
    # Import/export watchlist
    storage.import_watchlist_uploader()
    storage.export_watchlist_button()
    # Show current watchlist with remove buttons
    watchlist = st.session_state.get("watchlist", [])
    for sym in list(watchlist):
        cols = st.sidebar.columns([3, 1])
        cols[0].write(sym)
        if cols[1].button("✕", key=f"rm_{sym}"):
            storage.remove_from_watchlist(sym)
            st.sidebar.warning(f"Removed {sym} from watchlist.")
    # Top search bar
    st.title("Signal Watch")
    query = st.text_input("Search ticker or company", key="search_query")
    selected_symbol = st.session_state.get("selected_symbol")
    if query:
        suggestions = search.yahoo_search(query)
        if suggestions:
            option_labels = [f"{x['symbol']} — {x['name']} ({x['exchange']})" for x in suggestions]
            sel = st.selectbox("Matches", option_labels)
            if st.button("Open selected", key="open_selected"):
                idx = option_labels.index(sel)
                selected_symbol = suggestions[idx]["symbol"]
                st.session_state["selected_symbol"] = selected_symbol
        else:
            st.write("No matches found.")
    # Main content
    if selected_symbol:
        # Detail view
        st.header(selected_symbol)
        try:
            df, price_col = data.fetch(selected_symbol, tf_key)
            df = indicators.attach_indicators(df, price_col)
            fig = charts.build_chart(df, price_col, show_macd, show_rsi, show_bb, theme_dark)
            st.plotly_chart(fig, use_container_width=True)
            # Signal summary
            snap = signals.latest_snapshot(df, price_col)
            dots = state_dot(snap["macd"]) + " " + state_dot(snap["rsi"]) + " " + state_dot(snap["bb"])
            st.info(f"Signals: {dots} → {snap['majority'].value.upper()}")
        except Exception as e:
            st.error(str(e))
        if st.button("Back to Watchlist"):
            st.session_state.pop("selected_symbol", None)
            st.experimental_rerun()
    else:
        # Overview
        st.header("Overview")
        display_watchlist_overview(tf_key, show_macd, show_rsi, show_bb)


if __name__ == "__main__":
    run()
