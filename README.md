# Signal Watch

Signal Watch is a simple Streamlit application for monitoring stock
tickers using three classic technical indicators: MACD, RSI and
Bollinger Bands. It provides a watchlist overview with colour coded
signals and a detailed candlestick chart view with optional indicator
overlays. A majority vote of the individual indicator states is used
to produce a buy/sell/hold recommendation.

## Features

* **Free data:** uses the Yahoo Finance API via `yfinance` so there are
  no API keys or paid subscriptions required.
* **Watchlist:** add tickers to your personal watchlist, import/export
  lists as JSON and track signals at a glance.
* **Indicators:** toggle MACD, RSI and Bollinger Bands overlays on the
  chart. The latest state of each indicator is displayed as coloured
  dots (green=buy, yellow=hold, red=sell).
* **Majority rule:** two or more buy signals ⇒ BUY; two or more sell
  signals ⇒ SELL; otherwise HOLD.
* **Responsive:** supports dark mode and adapts to different screen sizes.

## Installation

Clone the repository and install the Python dependencies:

```bash
pip install -r requirements.txt
```

## Running the app

Use Streamlit to run the application:

```bash
streamlit run signal_watch/app.py
```

Then open your browser to the URL printed by Streamlit (typically
`http://localhost:8501`).

## Disclaimer

This project is for educational purposes only and does not constitute
investment advice. Data provided by Yahoo may be delayed or
inaccurate. Always do your own research before making investment
decisions.
