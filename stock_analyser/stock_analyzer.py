"""
Stock Analyzer — a learning project for the Gemini API.

This tool is NOT a stock predictor. It pulls real price history and recent
news headlines for a ticker, then asks Gemini to reason over that data and
produce a plain-English summary: recent trend, notable news, and things a
person might want to research further. It deliberately avoids asking Gemini
for a price target or buy/sell call — that would be a false promise of
certainty an LLM can't back up.

Setup:
    pip install -U google-genai yfinance
    export GEMINI_API_KEY="your-key-here"   # get one free at aistudio.google.com

Usage:
    python stock_analyzer.py AAPL
    python stock_analyzer.py TSLA --days 30
"""

import argparse
import io
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — required for headless environments

from matplotlib import ticker
import mplfinance as mpf
import yfinance as yf
from google import genai
from google.genai import errors as genai_errors

from stock_data import StockDataProvider, YahooFinanceStockDataProvider


def get_price_history(ticker: str, days: int):
    """Pull raw OHLCV price history as a pandas DataFrame."""
    return STOCK_DATA_PROVIDER.get_price_history(ticker, days)


def summarize_price_history(hist, ticker: str, days: int) -> str:
    """Turn a price history DataFrame into a compact text summary for the prompt."""
    start_price = hist["Close"].iloc[0]
    end_price = hist["Close"].iloc[-1]
    pct_change = (end_price - start_price) / start_price * 100
    high = hist["High"].max()
    low = hist["Low"].min()
    avg_volume = hist["Volume"].mean()

    summary = (
        f"Ticker: {ticker}\n"
        f"Period: last {days} trading days\n"
        f"Start price: ${start_price:.2f}\n"
        f"Latest price: ${end_price:.2f}\n"
        f"Change over period: {pct_change:+.2f}%\n"
        f"Period high: ${high:.2f}\n"
        f"Period low: ${low:.2f}\n"
        f"Average daily volume: {avg_volume:,.0f} shares"
    )
    return summary


def fetch_price_summary(ticker: str, days: int) -> str:
    """Convenience wrapper: fetch history and summarize it in one call."""
    hist = get_price_history(ticker, days)
    return summarize_price_history(hist, ticker, days)


def render_candlestick_png(hist, ticker: str) -> bytes:
    """Render a candlestick chart from a price history DataFrame and return it as PNG bytes.

    This is the in-memory version — useful when you want to embed the image
    (e.g. in an API JSON response) without writing a temp file to disk.

    Green candles = price closed higher than it opened that day.
    Red candles = price closed lower than it opened that day.
    The lines above/below each candle (wicks) show the day's high and low.
    A volume bar chart is included below the price panel.
    """
    buf = io.BytesIO()
    mpf.plot(
        hist,
        type="candle",
        style="yahoo",
        title=f"{ticker} - Last {len(hist)} Trading Days",
        ylabel="Price ($)",
        volume=True,
        savefig=dict(fname=buf, dpi=150, bbox_inches="tight", format="png"),
    )
    buf.seek(0)
    return buf.getvalue()


def plot_candlestick(hist, ticker: str, output_path: str) -> str:
    """Render a candlestick chart and save it to a file. Used by the CLI."""
    png_bytes = render_candlestick_png(hist, ticker)
    with open(output_path, "wb") as f:
        f.write(png_bytes)
    return output_path


def fetch_news_summary(ticker: str, max_items: int = 5) -> str:
    """Pull recent news headlines for the ticker via yfinance."""
    stock = yf.Ticker(ticker)
    try:
        news_items = stock.news[:max_items]
    except Exception:
        return "No recent news available."

    if not news_items:
        return "No recent news available."

    lines = []
    for item in news_items:
        content = item.get("content", item)  # yfinance news format varies by version
        title = content.get("title") or item.get("title", "Untitled")
        publisher = (
            content.get("provider", {}).get("displayName")
            if isinstance(content.get("provider"), dict)
            else item.get("publisher", "Unknown source")
        )
        lines.append(f"- \"{title}\" ({publisher})")

    return "\n".join(lines)


# Tried in order. gemini-3.5-flash is the main model; gemini-3.1-flash-lite
# is a lighter/cheaper fallback if the first one is overloaded or unavailable.
MODEL_FALLBACKS = ["gemini-3.5-flash", "gemini-3.1-flash-lite"]
STOCK_DATA_PROVIDER: StockDataProvider = YahooFinanceStockDataProvider()


def analyze_with_gemini(price_summary: str, news_summary: str, ticker: str) :
    """Send the collected data to Gemini and ask for a qualitative analysis.

    Retries on transient errors (like a 503 "model overloaded") with backoff,
    and falls back to a second model if the first one keeps failing.
    """
    client = genai.Client()  # reads GEMINI_API_KEY from environment

    system_instruction = """You are a financial research assistant. You write
        short, balanced analyses of stocks based on price data and news headlines.
        Never give a price target, a buy/sell recommendation, or any prediction of
        future price movement. Always make clear this is not financial advice."""

    prompt = f"""Analyse the following data for {ticker} and write a short report covering:
                1. What the recent price trend shows (a few sentences)
                2. What the news headlines suggest is currently affecting the company
                3. 2-3 specific things someone researching this stock further should look into

                PRICE DATA:
                {price_summary}

                RECENT NEWS HEADLINES:
                {news_summary}
                Write in plain English, suitable for a general audience. Keep it concise."""
    

    last_error = None
    for model in MODEL_FALLBACKS:
        for attempt in range(3):
            try:
                token_count=client.models.count_tokens(
                    model = model,
                    contents= prompt,
                )
                response = client.models.generate_content_stream(
                            model=model,contents=prompt,config={"system_instruction": system_instruction},)
                for chunk in response:
                    print(chunk.text, end="", flush=True)

                print("Gemini analysis complete. The token count for this request was:", token_count.total_tokens)
            except genai_errors.ServerError as e:
                # Transient issue (e.g. 503 overloaded) - wait and retry.
                last_error = e
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
            except genai_errors.ClientError as e:
                # Not found, bad request, etc. - retrying won't help, try next model.
                last_error = e
                break

    raise RuntimeError(f"All models failed. Last error: {last_error}")


def main():
    parser = argparse.ArgumentParser(description="Analyze a stock using real data + Gemini.")
    parser.add_argument("ticker", help="Stock ticker symbol, e.g. AAPL, TSLA, MSFT")
    parser.add_argument("--days", type=int, default=30, help="Number of trading days of history to pull (default: 30)")
    parser.add_argument("--no-chart", action="store_true", help="Skip generating the candlestick chart")
    args = parser.parse_args()

    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit(
            "Error: GEMINI_API_KEY environment variable not set.\n"
            "Get a free key at https://aistudio.google.com/apikey and run:\n"
            "  export GEMINI_API_KEY=\"your-key-here\""
        )

    ticker = args.ticker.upper()
    print(f"Fetching data for {ticker}...\n")

    try:
        hist = get_price_history(ticker, args.days)
    except ValueError as e:
        sys.exit(str(e))

    price_summary = summarize_price_history(hist, ticker, args.days)
    news_summary = fetch_news_summary(ticker)

    print("--- Price Summary ---")
    print(price_summary)
    print("\n--- Recent Headlines ---")
    print(news_summary)

    if not args.no_chart:
        chart_path = f"{ticker}_candlestick.png"
        plot_candlestick(hist, ticker, chart_path)
        print(f"\nCandlestick chart saved to: {chart_path}")
    
    print("\n--- Gemini Analysis ---")
    analyze_with_gemini(price_summary, news_summary, ticker)

    print(
        "\n(This is a learning project, not financial advice. "
        "Gemini's analysis is based only on the data shown above.)"
    )


if __name__ == "__main__":
    main()