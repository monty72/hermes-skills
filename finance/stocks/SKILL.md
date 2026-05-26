---
name: stocks
description: "Stock quotes, history, search, compare, crypto via Yahoo Finance."
version: 1.0.0
---

# Stocks

## Overview

Stock quotes, history, search, compare, and crypto via Yahoo Finance (no API key needed).

## Requirements

```bash
pip install yfinance
```

## Quote

```python
import yfinance as yf

ticker = yf.Ticker("AAPL")
info = ticker.info

print(f"Price: ${info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))}")
print(f"Change: {info.get('regularMarketChangePercent', 0):.2f}%")
print(f"Market Cap: ${info.get('marketCap', 0):,}")
print(f"PE Ratio: {info.get('trailingPE', 'N/A')}")
print(f"52W High: ${info.get('fiftyTwoWeekHigh', 'N/A')}")
print(f"52W Low: ${info.get('fiftyTwoWeekLow', 'N/A')}")
```

## History

```python
import yfinance as yf

ticker = yf.Ticker("AAPL")
hist = ticker.history(period="1mo")  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

print(hist.tail().to_string())
```

## Search

```python
from yfinance import search as yf_search

results = yf_search("Apple")
for r in results.get("quotes", [])[:5]:
    print(f"{r.get('symbol')} - {r.get('shortname')} ({r.get('exchange')})")
```

## Multiple Tickers

```python
import yfinance as yf

tickers = yf.Tickers("AAPL MSFT GOOGL")
for sym, ticker in tickers.tickers.items():
    info = ticker.info
    price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
    change = info.get('regularMarketChangePercent', 0)
    print(f"{sym}: ${price} ({change:+.2f}%)")
```

## Crypto

```python
import yfinance as yf

btc = yf.Ticker("BTC-USD")
info = btc.info
print(f"Bitcoin: ${info.get('currentPrice', 'N/A'):,}")

eth = yf.Ticker("ETH-USD")
info = eth.info
print(f"Ethereum: ${info.get('currentPrice', 'N/A'):,}")
```
