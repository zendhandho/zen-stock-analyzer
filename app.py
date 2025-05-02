import streamlit as st
import OpenAI
import yfinance as yf

# Initialize OpenAI client
import os
openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.ChatCompletion.create(
  model="gpt-4",
  messages=[{"role": "user", "content": prompt}],
  temperature=0.6
)
return response.choices[0].message["content"]
        "symbol": ticker_symbol,
        "price": info.get("currentPrice"),
        "pe_ratio": info.get("trailingPE"),
        "market_cap": info.get("marketCap"),
        "dividend_yield": info.get("dividendYield"),
        "52_week_high": info.get("fiftyTwoWeekHigh"),
        "52_week_low": info.get("fiftyTwoWeekLow"),
    }

def analyze_with_gpt(stock_data):
    prompt = f"""
You are a value investor like Warren Buffett or Monish Pabrai. Analyze the following stock:

Ticker: {stock_data['symbol']}
Price: {stock_data['price']}
P/E Ratio: {stock_data['pe_ratio']}
Market Cap: {stock_data['market_cap']}
Dividend Yield: {stock_data['dividend_yield']}
52-Week High: {stock_data['52_week_high']}
52-Week Low: {stock_data['52_week_low']}

Is this stock undervalued? Share your rationale in simple terms.
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    )
    return response.choices[0].message.content

# --- Streamlit UI ---
st.set_page_config(page_title="Zen Dhandho Stock Analyzer", layout="centered")
st.title("🧘 Zen Dhandho Stock Analyzer")
st.markdown("Wall Street-caliber guidance — without the $250K minimum.")

ticker = st.text_input("Enter a stock ticker (e.g., AAPL, MSFT, TSLA)")

if st.button("Analyze"):
    if not ticker:
        st.warning("Please enter a stock ticker.")
    else:
        with st.spinner("Fetching data and analyzing..."):
            stock_data = get_stock_data(ticker.upper())
            analysis = analyze_with_gpt(stock_data)
        st.subheader("📊 GPT Analysis")
        st.write(analysis)