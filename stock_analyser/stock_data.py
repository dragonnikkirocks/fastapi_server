from typing import Any, Optional, Protocol

import pandas as pd
import yfinance as yf


class StockDataProvider(Protocol):
    """Interface for retrieving stock price history."""

    def get_price_history(self, ticker: str, days: int) -> pd.DataFrame:
        ...


class YahooFinanceStockDataProvider:
    """Concrete implementation that reads price history from yfinance."""

    def __init__(self, client: Optional[Any] = None) -> None:
        self._client = client or yf

    def get_price_history(self, ticker: str, days: int) -> pd.DataFrame:
        stock = self._client.Ticker(ticker)
        hist = stock.history(period=f"{days}d")

        if hist.empty:
            raise ValueError(f"No price data found for ticker '{ticker}'. Check the symbol.")

        return hist


class MockStockDataProvider:
    """Simple in-memory provider for tests and local development."""

    def __init__(self, history_by_ticker: Optional[dict[str, pd.DataFrame]] = None) -> None:
        self._history_by_ticker = history_by_ticker or {}

    def register_history(self, ticker: str, history: pd.DataFrame) -> None:
        self._history_by_ticker[ticker.upper()] = history

    def get_price_history(self, ticker: str, days: int) -> pd.DataFrame:
        history = self._history_by_ticker.get(ticker.upper())
        if history is None:
            raise ValueError(f"No price data found for ticker '{ticker}'. Check the symbol.")

        if len(history) < days:
            return history

        return history.iloc[-days:]
