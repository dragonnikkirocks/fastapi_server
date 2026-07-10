# Stock Analyzer — Gemini API Learning Project

A small tool that pulls real stock price data and news headlines, then uses
Gemini to write a plain-English analysis. Built to teach you the basics of
the Gemini API: authentication, sending a prompt, and combining external
data with an LLM call.

**Important:** this does not predict future prices. No LLM can reliably do
that — it has no access to real-time market-moving information and stock
prices are influenced by far more than public news. This tool is for
learning the API and practicing "data + LLM reasoning" patterns, not for
making investment decisions.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Get a free Gemini API key at https://aistudio.google.com/apikey

3. Set it as an environment variable:
   ```bash
   export GEMINI_API_KEY="your-key-here"
   ```
   (On Windows: `set GEMINI_API_KEY=your-key-here`)

## Usage

```bash
python stock_analyzer.py AAPL
python stock_analyzer.py TSLA --days 60
```

## How it works

1. `fetch_price_summary()` — uses `yfinance` (free, no API key needed) to
   pull recent price history and compute basic stats: % change, high, low,
   average volume.
2. `fetch_news_summary()` — pulls a handful of recent news headlines for
   the ticker, also via `yfinance`.
3. `analyze_with_gemini()` — sends both summaries to Gemini in a single
   prompt and asks it to reason over them, explicitly instructing it NOT to
   give a price prediction or buy/sell call.

## Running it as a web API (FastAPI)

`api.py` wraps the same logic in a FastAPI server, so instead of a CLI call
you get an HTTP endpoint that returns JSON.

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-here"
uvicorn api:app --reload
```

Then open:
- `http://127.0.0.1:8000/analyze/AAPL` — runs the full analysis (price
  summary, news, Gemini analysis, and the candlestick chart) and returns it
  all as one JSON object
- `http://127.0.0.1:8000/analyze/TSLA?days=60` — customize the lookback window
- `http://127.0.0.1:8000/chart/AAPL` — returns just the candlestick chart
  as a raw PNG image (open this URL directly in a browser to view it)
- `http://127.0.0.1:8000/docs` — interactive docs FastAPI generates automatically; you can try requests right from the browser

This is the same pattern real products use: the LLM logic lives behind an
API, and a frontend (web app, mobile app, Slack bot, etc.) calls it instead
of running Python scripts directly.

## Candlestick chart

Both the CLI and the API generate a candlestick chart from the same price
DataFrame used for the analysis (via `mplfinance`):

- **CLI**: `python stock_analyzer.py AAPL` saves `AAPL_candlestick.png` in
  the current directory automatically. Use `--no-chart` to skip it.
- **API — `/analyze/{ticker}`**: the chart is embedded directly in the JSON
  response as `chart_base64` (see below for how to view it).
- **API — `/chart/{ticker}`**: returns just the raw PNG image — open the
  URL directly in a browser to view it, no decoding needed.

Each candle shows one trading day: the thick body is the open-to-close
range (green if it closed higher than it opened, red if lower), and the
thin wick above/below shows the day's high and low. A volume bar chart is
included below the price panel.

### Viewing the embedded chart from `/analyze`

`/analyze` returns the chart as `chart_base64` — a base64-encoded PNG string
inside the JSON. Raw JSON viewers (like curl or a browser tab) won't render
it as an image directly; you need to decode it. Two easy ways:

**In a browser console or HTML page**, turn it into a data URI:
```html
<img src="data:image/png;base64,PASTE_THE_STRING_HERE" />
```

**In Python**, decode and save it:
```python
import requests, base64

r = requests.get("http://127.0.0.1:8000/analyze/AAPL").json()
with open("chart.png", "wb") as f:
    f.write(base64.b64decode(r["chart_base64"]))
```

If you just want to *see* the chart quickly without dealing with base64,
use `/chart/AAPL` instead — it returns the raw image directly.

## Ideas to extend this (good next steps for learning the API)

There's a lot you could add here — this section is grouped by theme, with
a suggested order at the end if you're not sure where to start.

### Gemini API skills

**Prompt & request fundamentals** (build on what's already in the script):
- **System instructions**: instead of stuffing "you are a financial
  research assistant, don't give price predictions" into the user prompt
  every time, move that into a `system_instruction` parameter on the model
  config. Cleaner separation, and the standard pattern for any real app. -> done
- **Streaming**: switch `generate_content` to `generate_content_stream` so
  the analysis prints as it's generated, instead of all at once. -> done
- **Token counting**: use `client.models.count_tokens()` before sending a
  request to estimate cost, and display it in the UI ("this analysis will
  use ~X tokens"). Good habit for any real product. -> done
- **Safety settings**: explore the `safety_settings` config option — not
  critical for this app, but foundational for anything you build later. -> basic concept understood. Not planned to be integrated now

**Giving Gemini more capability:**
- **Function calling**: instead of fetching data yourself and stuffing it
  into the prompt, define `fetch_price_summary` and `fetch_news_summary` as
  tools and let Gemini decide when to call them.
- **Structured output**: ask Gemini to return JSON (e.g.
  `{"trend": "...", "key_news": [...], "watch_items": [...]}`) so you could
  build a simple web dashboard on top of it, instead of parsing free text.
- **Google Search grounding**: use Gemini's built-in Google Search tool
  instead of `yfinance` news, so the model can pull in live web context.
- **Multimodal input**: feed the model an image directly — e.g. upload a
  screenshot of a chart from another source and ask it to describe patterns
  it sees. Or pass a company's quarterly earnings report PDF straight to
  Gemini (it reads PDFs natively) and ask it to extract key figures.

**Bigger conceptual jumps:**
- **Multi-turn chat**: right now each call to `analyze_with_gemini()` is a
  single, stateless prompt. Using `client.chats.create()` instead of
  one-off `generate_content` calls would let a user ask follow-ups
  ("what about the last 90 days instead?") without repeating all the
  context — teaches you how conversation history is actually managed.
- **Multi-ticker comparison**: pass in 2-3 tickers and ask Gemini to
  compare them side by side — combines well with structured output.
- **Embeddings**: embed news headlines with Gemini's embedding model
  (`embed_content` — a different API surface than everything else here),
  store them, and build simple semantic search over past headlines for a
  ticker ("find articles about supply chain issues").
- **Context caching**: relevant once you're passing large, reused content
  repeatedly (e.g. a full 10-K filing) — Gemini can cache it server-side so
  you're not reprocessing it on every call.
- **Async / batch requests**: if you want to analyze many tickers at once,
  the Python SDK has async support (`client.aio.models.generate_content`) —
  useful to learn alongside FastAPI, which is async-native.
- **Thinking / reasoning effort**: Gemini's newer models support an
  adjustable "thinking" effort for harder reasoning tasks — worth trying on
  something like "compare these 3 tickers and reason about relative risk,"
  where more reasoning steps may produce a noticeably better answer.

### Making this a real app (broader backend/web skills)

- **Authentication**: right now anyone who can reach the server can hit
  every endpoint, including one that calls the (metered) Gemini API. The
  simplest first step is an API key check — FastAPI supports this cleanly
  via a "dependency": a function that checks a header (e.g.
  `X-API-Key`) against an expected value and runs before the endpoint. Look
  up `fastapi.Security` and `APIKeyHeader` for the standard pattern. Beyond
  that, `python-jose` + OAuth2 (FastAPI has built-in support via
  `OAuth2PasswordBearer`) is the next step up if you want real user
  accounts and login.
- **Rate limiting**: pairs naturally with auth — without it, one user (or
  a bug in a frontend) could burn through your Gemini quota fast. The
  `slowapi` package is a simple drop-in for FastAPI.
- **Caching**: if the same ticker gets requested repeatedly, you're paying
  for a fresh Gemini call and yfinance fetch every time. A simple in-memory
  cache (even just a dict with a timestamp) that reuses results for a few
  minutes teaches a pattern that matters a lot at real-world scale.
- **A better GUI**: the current `/view` page is plain server-rendered HTML.
  Natural upgrades, roughly in order of effort:
  - Add a simple `<form>` on the homepage so someone can type a ticker and
    hit submit, instead of editing the URL by hand.
  - Add a loading state — Gemini calls take a few seconds, so some
    JavaScript that shows a spinner while `/analyze` is in flight makes it
    feel much more responsive.
  - Move to a proper frontend (React, Vue, or even just vanilla JS) that
    calls `/analyze` for JSON and renders the chart, text, and layout
    however you like, instead of the server building HTML strings.
  - Add a ticker search/autocomplete instead of requiring an exact symbol.
- **Downloadable PDF report**: turn one analysis into a PDF a user can
  click to download. The `reportlab` or `fpdf2` libraries can build a PDF
  from scratch (embed the chart image, format the text sections); `WeasyPrint`
  is a good alternative if you'd rather write the report as HTML/CSS and
  convert it. In FastAPI, generate the PDF bytes in-memory and return them
  with `fastapi.responses.Response(content=pdf_bytes, media_type="application/pdf",
  headers={"Content-Disposition": "attachment; filename=AAPL_report.pdf"})`
  — that `Content-Disposition` header is what makes the browser download it
  instead of trying to display it inline. Add a "Download PDF" button on
  the `/view` page pointing at a new `/report/{ticker}` endpoint.
- **Persistence**: save each analysis (ticker, timestamp, summary, chart)
  to a database (SQLite is the easiest starting point) so users can look
  back at past analyses instead of only ever seeing the latest one.
- **Deployment**: once it feels solid locally, deploying it (Render,
  Fly.io, Railway, or a small VPS) with the `GEMINI_API_KEY` set as a
  secret environment variable — never hardcoded — is a good capstone step
  that teaches the last mile of "shipping" an API project.

### Trying other providers: Amazon Bedrock

Worth knowing about once you've got the Gemini version working: **Amazon
Bedrock** is AWS's managed API for foundation models — instead of one
provider, it gives you a single unified API to call models from Anthropic
(Claude), Meta (Llama), Mistral, Amazon (Nova), and others.

A few things to know before switching or adding it:

- **No free tier** — unlike Gemini's free rate-limited tier, Bedrock is
  pay-per-token from your very first request. New AWS accounts do get
  $200 in general AWS credit (split $100 signup / $100 for completing
  guided activities, expiring after 6 months), usable on Bedrock, but
  there's no ongoing free allotment for experimentation the way Gemini
  has.
- **Different auth model** — instead of a single `GEMINI_API_KEY`, Bedrock
  uses AWS IAM credentials (access key + secret, or an IAM role), via the
  `boto3` SDK. This is a genuinely useful thing to learn since IAM-based
  auth is how most AWS services work, not just Bedrock.
- **Why you'd use it anyway** — it's the natural choice if you're already
  building on AWS infrastructure (e.g. deploying this app on AWS later —
  see the Deployment idea above), need a model from a provider other than
  Google, or want compliance features (HIPAA eligibility, data residency,
  private networking via PrivateLink) that matter for regulated use cases.
  It's also a good way to compare how the *same* model (e.g. Claude)
  behaves when called through Bedrock vs. directly through Anthropic's own
  API.

**As a learning exercise**, a clean way to try this: add a second
`analyze_with_bedrock()` function alongside `analyze_with_gemini()` using
`boto3`'s `bedrock-runtime` client and its `converse()` API (Bedrock's
unified interface across model providers), then add a `?provider=gemini`
vs `?provider=bedrock` query parameter to the `/analyze` endpoint so you
can compare responses from different providers on the same data — a nice
introduction to building provider-agnostic LLM code, which matters a lot
if you ever build something you don't want locked into a single vendor.

### Suggested order to tackle these

If you're not sure where to start, roughly:

1. **System instructions** — quick, cleans up the prompt you already have.
2. **Streaming** — quick, immediately visible improvement to the CLI/API.
3. **Better GUI (form + loading state)** — makes the app pleasant to
   actually use, which makes everything after this more motivating.
4. **Structured output + function calling** — the two Gemini features that
   teach the most about how "agentic" apps are really built.
5. **Downloadable PDF report** — a satisfying, visible feature to ship.
6. **Authentication + rate limiting** — do these together once you're
   thinking about letting other people use it.
7. **Caching + persistence** — once you have real repeat usage to optimize
   for.
8. Everything else (multi-turn chat, embeddings, multimodal input, context
   caching, async/batch, deployment, trying Amazon Bedrock as a second
   provider) — pick based on what sounds most interesting once the basics
   are solid.