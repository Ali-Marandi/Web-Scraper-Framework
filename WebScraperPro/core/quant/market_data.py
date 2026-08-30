r"""
Quantitative Finance - Real Market Data Feed
==========================================
Fetches real-time and historical market data from free sources.

Providers:
    - Yahoo Finance (yfinance) — free, no API key, historical + real-time
    - Alpha Vantage — free tier (25 req/day), API key required
    - Manual CSV/JSON import

All data is normalized into TimeSeriesData for the QuantEngine pipeline.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class YahooFinanceProvider:
    """Fetch market data from Yahoo Finance via yfinance library.

    Parameters
    ----------
    session_timeout : int
        HTTP request timeout in seconds.
    retry_count : int
        Number of retries on failed requests.
    """

    def __init__(self, session_timeout: int = 30, retry_count: int = 3):
        self._timeout = session_timeout
        self._retry_count = retry_count
        self._yf = None

    def _get_yf(self):
        """Lazy import yfinance to avoid startup cost."""
        if self._yf is None:
            try:
                import yfinance as yf
                self._yf = yf
            except ImportError:
                raise RuntimeError(
                    "yfinance is not installed. Install it with: pip install yfinance"
                )
        return self._yf

    def fetch_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """Download historical OHLCV data.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. ``"AAPL"``, ``"GOOGL"``, ``"^GSPC"``).
        period : str
            Data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max.
        interval : str
            Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo.
        start, end : str, optional
            Start/end dates (``"YYYY-MM-DD"``). Overrides *period*.

        Returns
        -------
        pd.DataFrame
            OHLCV data with columns: Open, High, Low, Close, Volume.
        """
        yf = self._get_yf()
        ticker = yf.Ticker(symbol)
        for attempt in range(self._retry_count):
            try:
                df = ticker.history(
                    period=period,
                    interval=interval,
                    start=start,
                    end=end,
                    timeout=self._timeout,
                )
                if df.empty:
                    logger.warning("yfinance returned empty data for %s (attempt %d)", symbol, attempt + 1)
                    time.sleep(1)
                    continue
                df = df.reset_index()
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]
                df = df.rename(columns={"date": "date"})
                return df
            except Exception as exc:
                logger.warning("yfinance error for %s: %s (attempt %d)", symbol, exc, attempt + 1)
                time.sleep(2 ** attempt)
        return pd.DataFrame()

    def fetch_quote(self, symbol: str) -> Dict[str, Any]:
        """Get latest quote snapshot for a single symbol.

        Returns
        -------
        dict with keys: symbol, price, change, change_pct, volume, market_cap,
        high_52w, low_52w, timestamp.
        """
        yf = self._get_yf()
        ticker = yf.Ticker(symbol)
        try:
            info = ticker.fast_info
            hist = ticker.history(period="2d")
            if hist.empty:
                return {"error": f"No data for {symbol}"}
            price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
            change = price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
            return {
                "symbol": symbol.upper(),
                "price": round(price, 4),
                "change": round(change, 4),
                "change_pct": round(change_pct, 2),
                "volume": int(info.last_volume) if hasattr(info, 'last_volume') else 0,
                "market_cap": getattr(info, 'market_cap', None),
                "high_52w": getattr(info, 'fifty_two_week_high', None),
                "low_52w": getattr(info, 'fifty_two_week_low', None),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            return {"error": str(exc)}

    def fetch_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch quotes for multiple symbols."""
        results = {}
        for sym in symbols:
            results[sym.upper()] = self.fetch_quote(sym)
        return results

    def search_symbols(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search for symbols matching *query* (yfinance search is limited).

        Returns list of dicts with keys: symbol, name, type.
        """
        yf = self._get_yf()
        try:
            ticker = yf.Ticker(query)
            info = ticker.info
            name = info.get("shortName", info.get("longName", query))
            return [{"symbol": query.upper(), "name": name, "type": "stock"}]
        except Exception:
            return [{"symbol": query.upper(), "name": query, "type": "unknown"}]


class AlphaVantageProvider:
    """Fetch market data from Alpha Vantage API.

    Parameters
    ----------
    api_key : str
        Alpha Vantage API key (free at alphavantage.co).
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str = ""):
        self._api_key = api_key or os.environ.get("ALPHA_VANTAGE_KEY", "demo")

    def fetch_daily(
        self, symbol: str, outputsize: str = "compact"
    ) -> pd.DataFrame:
        """Fetch daily OHLCV data.

        Parameters
        ----------
        symbol : str
            Ticker symbol.
        outputsize : str
            ``"compact"`` (last 100 days) or ``"full"`` (20+ years).
        """
        import requests
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": outputsize,
            "apikey": self._api_key,
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            data = resp.json()
            ts_key = "Time Series (Daily)"
            if ts_key not in data:
                err = data.get("Note", data.get("Error Message", "Unknown error"))
                logger.warning("Alpha Vantage error: %s", err)
                return pd.DataFrame()
            rows = []
            for date_str, vals in data[ts_key].items():
                rows.append({
                    "date": date_str,
                    "open": float(vals["1. open"]),
                    "high": float(vals["2. high"]),
                    "low": float(vals["3. low"]),
                    "close": float(vals["4. close"]),
                    "volume": int(vals["6. volume"]),
                })
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            return df
        except Exception as exc:
            logger.error("Alpha Vantage fetch error: %s", exc)
            return pd.DataFrame()

    def fetch_quote(self, symbol: str) -> Dict[str, Any]:
        """Get global quote for a symbol."""
        import requests
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self._api_key,
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=15)
            data = resp.json()
            q = data.get("Global Quote", {})
            if not q:
                return {"error": "No quote data returned"}
            price = float(q.get("05. price", 0))
            prev_close = float(q.get("08. previous close", price))
            change = float(q.get("09. change", 0))
            change_pct = float(q.get("10. change percent", "0%").replace("%", ""))
            return {
                "symbol": symbol.upper(),
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "volume": int(q.get("06. volume", 0)),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            return {"error": str(exc)}


class MarketDataFeed:
    """Unified market data interface for the QuantEngine.

    Supports multiple providers and automatic normalization into
    ``TimeSeriesData`` objects.

    Parameters
    ----------
    alpha_vantage_key : str, optional
        API key for Alpha Vantage (falls back to env var).
    """

    def __init__(self, alpha_vantage_key: str = ""):
        self._yfinance = YahooFinanceProvider()
        self._av = AlphaVantageProvider(alpha_vantage_key)
        self._fetch_cache: Dict[str, Tuple[float, pd.DataFrame]] = {}
        self._cache_ttl = 300.0  # 5 minutes

    def fetch_yahoo(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch historical data from Yahoo Finance."""
        cache_key = f"yf_{symbol}_{period}_{interval}"
        cached = self._fetch_cache.get(cache_key)
        if cached and (time.time() - cached[0]) < self._cache_ttl:
            return cached[1].copy()
        df = self._yfinance.fetch_history(symbol, period=period, interval=interval)
        self._fetch_cache[cache_key] = (time.time(), df)
        return df

    def fetch_alpha_vantage(self, symbol: str, outputsize: str = "compact") -> pd.DataFrame:
        """Fetch historical data from Alpha Vantage."""
        cache_key = f"av_{symbol}_{outputsize}"
        cached = self._fetch_cache.get(cache_key)
        if cached and (time.time() - cached[0]) < self._cache_ttl:
            return cached[1].copy()
        df = self._av.fetch_daily(symbol, outputsize=outputsize)
        self._fetch_cache[cache_key] = (time.time(), df)
        return df

    def get_quote(self, symbol: str, provider: str = "yahoo") -> Dict[str, Any]:
        """Get latest quote for a symbol.

        Parameters
        ----------
        symbol : str
            Ticker symbol.
        provider : str
            ``"yahoo"`` or ``"alpha_vantage"``.
        """
        if provider == "alpha_vantage":
            return self._av.fetch_quote(symbol)
        return self._yfinance.fetch_quote(symbol)

    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch quotes for multiple symbols via Yahoo."""
        return self._yfinance.fetch_batch_quotes(symbols)

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search for symbols (Yahoo only)."""
        return self._yfinance.search_symbols(query, max_results)

    def popular_tickers(self) -> List[Dict[str, str]]:
        """Return a curated list of popular tickers for quick access."""
        return [
            {"symbol": "AAPL", "name": "Apple Inc.", "type": "stock"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "type": "stock"},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "type": "stock"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "type": "stock"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "type": "stock"},
            {"symbol": "META", "name": "Meta Platforms", "type": "stock"},
            {"symbol": "NVDA", "name": "NVIDIA Corp.", "type": "stock"},
            {"symbol": "JPM", "name": "JPMorgan Chase", "type": "stock"},
            {"symbol": "V", "name": "Visa Inc.", "type": "stock"},
            {"symbol": "^GSPC", "name": "S&P 500 Index", "type": "index"},
            {"symbol": "^DJI", "name": "Dow Jones Industrial", "type": "index"},
            {"symbol": "^IXIC", "name": "NASDAQ Composite", "type": "index"},
            {"symbol": "GC=F", "name": "Gold Futures", "type": "commodity"},
            {"symbol": "CL=F", "name": "Crude Oil Futures", "type": "commodity"},
            {"symbol": "BTC-USD", "name": "Bitcoin USD", "type": "crypto"},
            {"symbol": "ETH-USD", "name": "Ethereum USD", "type": "crypto"},
        ]

    def load_into_quant_data(self, data_manager, symbol: str,
                              provider: str = "yahoo", period: str = "1y") -> Dict[str, Any]:
        """Fetch data and load directly into a QuantDataManager instance.

        Returns
        -------
        dict with status, symbol, rows, and dataset_name.
        """
        if provider == "alpha_vantage":
            df = self.fetch_alpha_vantage(symbol)
        else:
            df = self.fetch_yahoo(symbol, period=period)

        if df.empty:
            return {"error": f"No data fetched for {symbol}"}

        value_col = "close" if "close" in df.columns else None
        date_col = "date" if "date" in df.columns else None

        if not value_col:
            return {"error": "No 'close' column in fetched data"}

        tsd = data_manager.add_from_dataframe(
            name=symbol.upper(),
            df=df,
            value_column=value_col,
            date_column=date_col or "",
            frequency="daily",
            source=f"{provider}_live",
            fetched_at=datetime.now().isoformat(),
        )

        return {
            "status": "ok",
            "symbol": symbol.upper(),
            "dataset_name": tsd.name,
            "rows": tsd.n_observations,
            "start": str(tsd.dates[0]) if len(tsd.dates) > 0 else None,
            "end": str(tsd.dates[-1]) if len(tsd.dates) > 0 else None,
            "provider": provider,
        }
