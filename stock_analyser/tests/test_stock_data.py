import pandas as pd
import pytest

from stock_data import MockStockDataProvider, YahooFinanceStockDataProvider


def make_history(length: int = 5) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Close": list(range(1, length + 1)),
            "High": list(range(10, 10 + length)),
            "Low": list(range(100, 100 + length)),
            "Volume": [1000 + i for i in range(length)],
        }
    )


def test_mock_provider_returns_recent_slice_for_requested_days() -> None:
    provider = MockStockDataProvider()
    history = make_history(5)
    provider.register_history("AAPL", history)

    result = provider.get_price_history("aapl", 3)

    assert result.equals(history.iloc[-3:])


def test_mock_provider_returns_full_history_when_days_exceed_length() -> None:
    provider = MockStockDataProvider()
    history = make_history(3)
    provider.register_history("MSFT", history)

    result = provider.get_price_history("MSFT", 10)

    assert result.equals(history)


def test_mock_provider_raises_for_unknown_ticker() -> None:
    provider = MockStockDataProvider()

    with pytest.raises(ValueError, match="No price data found"):
        provider.get_price_history("TSLA", 5)


def test_yahoo_provider_uses_injected_client() -> None:
    class FakeTicker:
        def __init__(self, ticker: str) -> None:
            self.ticker = ticker

        def history(self, period: str) -> pd.DataFrame:
            return pd.DataFrame({"Close": [1.0]}, index=[0])

    class FakeClient:
        def Ticker(self, ticker: str) -> FakeTicker:
            return FakeTicker(ticker)

    provider = YahooFinanceStockDataProvider(client=FakeClient())

    result = provider.get_price_history("AAPL", 5)

    assert result.iloc[0]["Close"] == 1.0
