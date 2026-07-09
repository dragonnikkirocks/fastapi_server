import matplotlib
matplotlib.use("Agg")   # add this before importing mplfinance

import yfinance as yf
import mplfinance as mpf

hist = yf.Ticker("AAPL").history(period="30d")
mpf.plot(hist, type="candle", style="yahoo", volume=True,
         savefig=dict(fname="test.png", dpi=150, bbox_inches="tight"))
print("done")