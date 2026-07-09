"""
Diagnostic script — run this exactly as-is and paste the full output back.
It isolates each step so we can see precisely where things go wrong.
"""

import os
import sys
import traceback

print("=" * 50)
print("STEP 0: Environment info")
print("=" * 50)
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Current working directory:", os.getcwd())

print("\n" + "=" * 50)
print("STEP 1: Checking imports")
print("=" * 50)
try:
    import matplotlib
    matplotlib.use("Agg")
    print("matplotlib OK, version:", matplotlib.__version__)
    print("matplotlib backend:", matplotlib.get_backend())
except Exception:
    print("FAILED to import/configure matplotlib:")
    traceback.print_exc()
    sys.exit(1)

try:
    import mplfinance as mpf
    print("mplfinance OK, version:", mpf.__version__)
except Exception:
    print("FAILED to import mplfinance:")
    traceback.print_exc()
    sys.exit(1)

try:
    import yfinance as yf
    print("yfinance OK, version:", yf.__version__)
except Exception:
    print("FAILED to import yfinance:")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("STEP 2: Fetching real data for AAPL")
print("=" * 50)
try:
    stock = yf.Ticker("AAPL")
    hist = stock.history(period="30d")
    print("Rows fetched:", len(hist))
    print(hist.head())
    if hist.empty:
        print("WARNING: DataFrame is empty. This is likely a network/data issue, not a plotting issue.")
        sys.exit(1)
except Exception:
    print("FAILED to fetch data:")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("STEP 3: Generating candlestick chart")
print("=" * 50)
output_path = os.path.join(os.getcwd(), "diagnostic_test.png")
print("Will attempt to save to:", output_path)

try:
    mpf.plot(
        hist,
        type="candle",
        style="yahoo",
        title="AAPL Diagnostic Test",
        ylabel="Price ($)",
        volume=True,
        savefig=dict(fname=output_path, dpi=150, bbox_inches="tight"),
    )
    print("mpf.plot() call completed without raising an exception.")
except Exception:
    print("FAILED during mpf.plot():")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("STEP 4: Verifying file exists")
print("=" * 50)
if os.path.exists(output_path):
    size = os.path.getsize(output_path)
    print(f"SUCCESS: File exists at {output_path} ({size} bytes)")
else:
    print(f"FAILURE: File does NOT exist at {output_path}, even though no exception was raised.")
    print("This would indicate a permissions issue or an unusual filesystem/sandboxing setup.")