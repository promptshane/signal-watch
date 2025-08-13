"""
Ticker search via Yahoo Finance free endpoint.

This module provides a thin wrapper around the public search endpoint
available on query1.finance.yahoo.com. It returns a list of matching
tickers along with their names and exchanges. No API key is required.

It is used by the Streamlit app to offer autocomplete suggestions when
the user types a query in the search box.
"""

from __future__ import annotations

from typing import List, Dict

import requests


def yahoo_search(query: str, limit: int = 8) -> List[Dict[str, str]]:
    """Search for tickers matching the query using Yahoo Finance.

    Args:
        query: Partial ticker symbol or company name.
        limit: Maximum number of results to return.

    Returns:
        A list of dictionaries each containing 'symbol', 'name' and
        'exchange'. Only ASCII symbols are returned to avoid exotic
        tickers.
    """
    if not query:
        return []
    url = "https://query1.finance.yahoo.com/v1/finance/search"
    params = {"q": query, "quotesCount": limit, "newsCount": 0}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        out = []
        for q in r.json().get("quotes", []):
            sym = q.get("symbol")
            name = q.get("shortname") or q.get("longname") or ""
            exch = q.get("exchDisp") or q.get("exchange") or ""
            if sym and sym.isascii():
                out.append({"symbol": sym, "name": name, "exchange": exch})
        return out
    except Exception:
        # In case of any error, return an empty list
        return []
