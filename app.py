import streamlit as st
import os
import time
import requests
import openai

# ─── Load Secrets ─────────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
YH_API_KEY  = os.getenv("YH_API_KEY")
YH_API_HOST = os.getenv("YH_API_HOST")  # e.g. "yahoo-finance15.p.rapidapi.com"

# ─── Fetcher: /v1/market/quotes (symbols) with retry, backoff & cache ─────────
@st.cache_data(ttl=3600)
def get_stock_data(ticker_symbol: str):
    """
    Fetches real-time quotes from the paid Yahoo Finance (RapidAPI) endpoint:
      GET https://{YH_API_HOST}/v1/market/quotes?symbols=<ticker_symbol>
    Retries on 429 with backoff. Returns dict or None.
    """
    url = f"https://{YH_API_HOST}/v1/market/quotes"
    headers = {
        "X-RapidAPI-Key":  YH_API_KEY,
        "X-RapidAPI-Host": YH_API_HOST
    }
    params = {"symbols": ticker_symbol}

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        time.sleep(1)  # space out requests
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
        except requests.HTTPError:
            if resp.status_code == 429 and attempt < max_attempts:
                backoff = 5 * attempt
                st.warning(f"Rate limited (429). Waiting {backoff}s before retry…")
                time.sleep(backoff)
                continue
            return None
        except Exception:
            if attempt < max_attempts:
                time.sleep(5)
                continue
            return None

        payload = resp.json()
        # The real-time quotes endpoint returns under "data"
        results = payload.get("data") or payload.get("quoteResponse", {}).get("result", [])
        if not results:
            return None

        info = results[0]
        return {
            "symbol":         info.get("symbol"),
            "price":          info.get("regularMarketPrice"),
            "pe_ratio":       info.get("trailingPE"),
            "market_cap":     info.get("marketCap"),
            "dividend_yield": info.get("dividendYield"),
            "52_week_high":   info.get("fiftyTwoWeekHigh"),
            "52_week_low":    info.get("fiftyTwoWeekLow"),
        }

# ─── GPT Analysis ──────────────────────────────────────────────────────────────
def analyze_with_gpt(stock_data: dict) -> str:
    prompt = f"""
You are a value investor like Warren Buffett or Mohnish Pabrai. Analyze the following stock:

Ticker: {stock_data['symbol']}
Price: {stock_data['price']}
P/E Ratio: {stock_data['pe_ratio']}
Market Cap: {stock_data['market_cap']}
Dividend Yield: {stock_data['dividend_yield']}
52-Week High: {stock_data['52_week_high']}
52-Week Low: {stock_data['52_week_low']}

Is this stock undervalued? Share your rationale in simple terms.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    )
    return response.choices[0].message.content  # v0.28 syntax

# ─── Streamlit UI ────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Zen Dhandho Stock Analyzer", layout="centered")
    st.title("🧘 Zen Dhandho Stock Analyzer")
    st.markdown("Wall Street-caliber guidance — without the $250K minimum.")

    ticker = st.text_input("Enter a stock ticker (e.g., AAPL, MSFT, TSLA)")

    if st.button("Analyze"):
        if not ticker:
            st.warning("Please enter a stock ticker.")
            return

        with st.spinner("Fetching data and analyzing…"):
            stock_data = get_stock_data(ticker.upper())
            if stock_data is None:
                st.error("🚫 Unable to fetch data (empty or rate-limited). Try again shortly.")
            else:
                analysis = analyze_with_gpt(stock_data)
                st.subheader("📊 GPT Analysis")
                st.write(analysis)

if __name__ == "__main__":
    main()