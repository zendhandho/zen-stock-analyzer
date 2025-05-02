import streamlit as st
import os
import time
import requests
import openai

# ─── Load Secrets ─────────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
YH_API_KEY  = os.getenv("YH_API_KEY")
YH_API_HOST = os.getenv("YH_API_HOST")  # e.g. "yahoo-finance15.p.rapidapi.com"

def get_stock_data_debug(ticker_symbol: str):
    """
    Debug version (no cache) that prints URL, headers, params, status, and body.
    """
    url = f"https://{YH_API_HOST}/api/v1/market/quote"
    headers = {
        "X-RapidAPI-Key":  YH_API_KEY,
        "X-RapidAPI-Host": YH_API_HOST
    }
    params = {"ticker": ticker_symbol, "type": "STOCKS"}

    # Show exactly what we’re calling
    st.write("▶️ URL:", url)
    st.write("▶️ Headers:", headers)
    st.write("▶️ Params:", params)

    # Sleep to avoid bursts
    time.sleep(1)

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        st.write("▶️ Status code:", resp.status_code)
        st.write("▶️ Response body:", resp.text[:500])
        resp.raise_for_status()
    except Exception as e:
        st.error(f"Fetch exception: {e}")
        return None

    payload = resp.json()
    # Try common paths
    results = (
        payload.get("data") or
        payload.get("quoteResponse", {}).get("result") or
        payload.get("result") or
        payload.get("quote")
    )
    st.write("▶️ Parsed results:", results)

    if not results:
        return None

    info = results[0] if isinstance(results, list) else results
    return {
        "symbol":       info.get("symbol"),
        "price":        info.get("regularMarketPrice") or info.get("price"),
        "pe_ratio":     info.get("trailingPE"),
        "market_cap":   info.get("marketCap"),
        "dividend_yield":info.get("dividendYield"),
        "52_week_high": info.get("fiftyTwoWeekHigh"),
        "52_week_low":  info.get("fiftyTwoWeekLow"),
    }

def main():
    st.title("🧘 Zen Dhandho Stock Analyzer (DEBUG MODE)")
    st.markdown("🔍 Showing raw request/response info below")

    ticker = st.text_input("Enter a ticker (e.g. AAPL)")
    if st.button("Debug Fetch"):
        if not ticker:
            st.warning("Please enter a stock ticker.")
            return

        data = get_stock_data_debug(ticker.upper())
        st.write("▶️ Final stock_data dict:", data)

if __name__ == "__main__":
    main()