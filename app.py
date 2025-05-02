import streamlit as st
import os
import time
import requests
import openai

# ─── Load Secrets ─────────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
YH_API_KEY    = os.getenv("YH_API_KEY")
YH_API_HOST   = os.getenv("YH_API_HOST")  # e.g. "yahoo-finance15.p.rapidapi.com"

# ─── Stock Fetcher with RapidAPI “real-time quotes” ───────────────────────────
@st.cache_data(ttl=3600)
def get_stock_data(ticker_symbol: str):
    """
    Calls the paid RapidAPI endpoint exactly as in the cURL snippet:
      GET https://{YH_API_HOST}/api/v1/market/quotes
        ?ticker=<ticker_symbol>&type=STOCKS
    Retries on 429, then parses either "quoteResponse" or "data".
    """
    url = f"https://{YH_API_HOST}/api/v1/market/quotes"
    headers = {
        "X-RapidAPI-Key":  YH_API_KEY,
        "X-RapidAPI-Host": YH_API_HOST
    }
    params = {
        "ticker": ticker_symbol,
        "type":   "STOCKS"
    }

    for attempt in range(1, 4):
        time.sleep(1)  # space out calls
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
        except requests.HTTPError as e:
            if resp.status_code == 429 and attempt < 3:
                backoff = 5 * attempt
                st.warning(f"Rate limited—retrying in {backoff}s…")
                time.sleep(backoff)
                continue
            return None
        except Exception:
            if attempt < 3:
                time.sleep(5)
                continue
            return None

        payload = resp.json()
        # first try the RapidAPI “data” array
        results = payload.get("data")
        # then try the classic Yahoo style
        if not results:
            results = payload.get("quoteResponse", {}).get("result")

        if not results:
            return None

        # sometimes it’s a dict, sometimes a list
        info = results[0] if isinstance(results, list) else results
        return {
            "symbol":         info.get("symbol"),
            "price":          info.get("regularMarketPrice") or info.get("price"),
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
        messages=[{"role":"user","content":prompt}],
        temperature=0.6
    )
    return response.choices[0].message.content

# ─── Streamlit UI ────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Zen Dhandho Stock Analyzer", layout="centered")
    st.title("🧘 Zen Dhandho Stock Analyzer")
    st.markdown("Wall Street-caliber guidance — no $250K minimum.")

    ticker = st.text_input("Enter a stock ticker (e.g., AAPL, MSFT, TSLA)")
    if st.button("Analyze"):
        if not ticker:
            st.warning("Please enter a stock ticker.")
            return

        with st.spinner("Fetching data…"):
            sd = get_stock_data(ticker.upper())
            if sd is None:
                st.error("🚫 Unable to fetch data. Check host/key or retry in a minute.")
            else:
                st.subheader("📊 GPT Analysis")
                st.write(analyze_with_gpt(sd))

if __name__ == "__main__":
    main()