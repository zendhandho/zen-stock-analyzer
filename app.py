import streamlit as st
import os, time, requests, openai

# ─── Load secrets ──────────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
YH_API_KEY  = os.getenv("YH_API_KEY")
YH_API_HOST = os.getenv("YH_API_HOST")  # e.g. "yahoo-finance15.p.rapidapi.com"

@st.cache_data(ttl=3600)
def get_stock_data(ticker_symbol: str):
    """
    Calls the paid RapidAPI endpoint:
      GET https://{YH_API_HOST}/api/v1/market/quotes?symbols=<ticker_symbol>
    Retries on 429, then parses the 'data' array and uses 'lastPrice'.
    """
    url = f"https://{YH_API_HOST}/api/v1/market/quotes"
    headers = {
        "X-RapidAPI-Key":  YH_API_KEY,
        "X-RapidAPI-Host": YH_API_HOST
    }
    params = {"symbols": ticker_symbol}

    for attempt in range(1, 4):
        time.sleep(1)
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            r.raise_for_status()
        except requests.HTTPError:
            if r.status_code == 429 and attempt < 3:
                backoff = 5 * attempt
                st.warning(f"Rate-limited, retrying in {backoff}s…")
                time.sleep(backoff)
                continue
            return None
        except Exception:
            if attempt < 3:
                time.sleep(5)
                continue
            return None

        data = r.json().get("data", [])
        if not data:
            return None

        info = data[0]
        return {
            "symbol":       info.get("symbol"),
            "price":        info.get("lastPrice", info.get("regularMarketPrice")),
            "pe_ratio":     info.get("trailingPE"),
            "market_cap":   info.get("marketCap"),
            "dividend_yield": info.get("dividendYield"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low":  info.get("fiftyTwoWeekLow"),
        }

def analyze_with_gpt(sd: dict) -> str:
    prompt = f"""
You are a value investor like Warren Buffett or Mohnish Pabrai. Analyze the following:

Ticker: {sd['symbol']}
Price: {sd['price']}
P/E Ratio: {sd['pe_ratio']}
Market Cap: {sd['market_cap']}
Dividend Yield: {sd['dividend_yield']}
52-Week High: {sd['52_week_high']}
52-Week Low: {sd['52_week_low']}

Is this undervalued? Explain simply.
"""
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}],
        temperature=0.6
    )
    return res.choices[0].message.content

def main():
    st.set_page_config(page_title="Zen Dhandho Stock Analyzer")
    st.title("🧘 Zen Dhandho Stock Analyzer")
    st.markdown("Wall Street-caliber guidance — without the $250K minimum.")

    t = st.text_input("Enter ticker (e.g. AAPL, MSFT)")
    if st.button("Analyze"):
        if not t:
            st.warning("Please enter a ticker.")
            return
        with st.spinner("Fetching…"):
            sd = get_stock_data(t.upper())
            if not sd:
                st.error("🚫 Couldn’t fetch live data. Check host/key or retry in a minute.")
            else:
                st.subheader("📊 GPT Analysis")
                st.write(analyze_with_gpt(sd))

if __name__ == "__main__":
    main()