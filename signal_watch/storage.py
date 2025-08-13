"""
Watchlist persistence helpers using Streamlit session state.

This module provides simple functions to manage a list of tickers in
the user's session state. It also exposes functions to import and
export the watchlist as JSON via Streamlit UI components.

No external backend is used; watchlists are stored in memory while
the Streamlit app is running. Users can export and later import
watchlists to persist them across sessions if desired.
"""

from __future__ import annotations

import json

import streamlit as st


def init_watchlist() -> None:
    """Initialise the watchlist in session state if not present."""
    st.session_state.setdefault("watchlist", [])


def add_to_watchlist(sym: str) -> None:
    """Add a symbol to the watchlist if it's not already present."""
    sym = sym.upper()
    wl = st.session_state.get("watchlist", [])
    if sym and sym not in wl:
        wl.append(sym)
        st.session_state["watchlist"] = wl


def remove_from_watchlist(sym: str) -> None:
    """Remove a symbol from the watchlist."""
    sym = sym.upper()
    wl = st.session_state.get("watchlist", [])
    st.session_state["watchlist"] = [s for s in wl if s != sym]


def export_watchlist_button() -> None:
    """Render a button that exports the watchlist to a JSON download."""
    wl = st.session_state.get("watchlist", [])
    data = {"watchlist": wl}
    st.download_button(
        label="Export Watchlist",
        data=json.dumps(data, indent=2),
        file_name="watchlist.json",
        mime="application/json",
    )


def import_watchlist_uploader() -> None:
    """Render an uploader that imports a watchlist from JSON."""
    f = st.file_uploader("Import Watchlist JSON", type="json")
    if f is not None:
        try:
            obj = json.load(f)
            if isinstance(obj, dict) and "watchlist" in obj:
                wl = list(dict.fromkeys([s.upper() for s in obj["watchlist"] if isinstance(s, str)]))
                st.session_state["watchlist"] = wl
                st.success("Imported watchlist.")
        except Exception as e:
            st.error(f"Failed to import watchlist: {e}")
