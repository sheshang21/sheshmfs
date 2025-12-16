import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import requests
from io import StringIO
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(page_title="Indian Stock Analyzer", layout="wide", page_icon="📈")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .positive {
        color: #00c853;
        font-weight: bold;
    }
    .negative {
        color: #ff1744;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analyzed_stocks' not in st.session_state:
    st.session_state.analyzed_stocks = None
if 'uploaded_df' not in st.session_state:
    st.session_state.uploaded_df = None

def fetch_stock_data(ticker, period='3mo'):
    """Fetch stock data from Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return None, None
        info = stock.info
        return hist, info
    except Exception as e:
        return None, None

def calculate_technical_indicators(df):
    """Calculate technical indicators"""
    if df is None or len(df) < 20:
        return None
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Moving Averages
    sma_20 = df['Close'].rolling(window=20).mean()
    sma_50 = df['Close'].rolling(window=50).mean() if len(df) >= 50 else None
    
    # Volume analysis
    avg_volume = df['Volume'].rolling(window=20).mean()
    volume_ratio = df['Volume'].iloc[-1] / avg_volume.iloc[-1] if avg_volume.iloc[-1] > 0 else 0
    
    # Price momentum
    price_change_5d = ((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5] * 100) if len(df) >= 5 else 0
    price_change_20d = ((df['Close'].iloc[-1] - df['Close'].iloc[-20]) / df['Close'].iloc[-20] * 100) if len(df) >= 20 else 0
    
    # Volatility
    volatility = df['Close'].pct_change().std() * np.sqrt(252) * 100
    
    return {
        'rsi': rsi.iloc[-1] if not rsi.empty else 50,
        'sma_20': sma_20.iloc[-1] if not sma_20.empty else df['Close'].iloc[-1],
        'sma_50': sma_50.iloc[-1] if sma_50 is not None and not sma_50.empty else None,
        'volume_ratio': volume_ratio,
        'price_change_5d': price_change_5d,
        'price_change_20d': price_change_20d,
        'volatility': volatility,
        'avg_volume': avg_volume.iloc[-1] if not avg_volume.empty else 0
    }

def calculate_probability_score(current_price, indicators, info):
    """Calculate probability score for upward movement"""
    score = 0
    max_score = 100
    
    if indicators is None:
        return 0
    
    # RSI analysis (oversold = bullish)
    rsi = indicators['rsi']
    if 30 <= rsi <= 50:
        score += 20
    elif 50 < rsi <= 60:
        score += 15
    elif rsi < 30:
        score += 25
    
    # Moving average crossover
    if indicators['sma_50'] is not None:
        if current_price > indicators['sma_20'] > indicators['sma_50']:
            score += 20
        elif current_price > indicators['sma_20']:
            score += 10
    else:
        if current_price > indicators['sma_20']:
            score += 15
    
    # Volume surge
    if indicators['volume_ratio'] > 1.5:
        score += 15
    elif indicators['volume_ratio'] > 1.2:
        score += 10
    
    # Momentum
    if indicators['price_change_5d'] > 2:
        score += 10
    elif indicators['price_change_5d'] > 0:
        score += 5
    
    # Recent trend
    if indicators['price_change_20d'] > 5:
        score += 10
    elif indicators['price_change_20d'] > 0:
        score += 5
    
    # Volatility (moderate volatility is good)
    if 20 < indicators['volatility'] < 50:
        score += 10
    elif indicators['volatility'] <= 20:
        score += 5
    
    return min(score, max_score)

def analyze_single_stock(row):
    """Analyze a single stock"""
    try:
        ticker = row['Ticker']
        
        # Try both .NS (NSE) and .BO (BSE) suffixes
        for suffix in ['.NS', '.BO']:
            full_ticker = f"{ticker}{suffix}"
            hist, info = fetch_stock_data(full_ticker, period='3mo')
            
            if hist is not None and not hist.empty:
                break
        else:
            return None
        
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
        
        # Calculate indicators
        indicators = calculate_technical_indicators(hist)
        
        if indicators is None:
            return None
        
        # Calculate probability score
        prob_score = calculate_probability_score(current_price, indicators, info)
        
        # Calculate potential targets
        target_20rs = current_price + 20
        target_3pct = current_price * 1.03
        percent_change_20rs = (20 / current_price) * 100
        
        # Check if it meets criteria
        meets_criteria = (
            prob_score >= 50 and  # Minimum probability threshold
            (indicators['rsi'] < 70) and  # Not overbought
            (indicators['price_change_20d'] > -10)  # Not in severe downtrend
        )
        
        if not meets_criteria:
            return None
        
        return {
            'Ticker': full_ticker,
            'Company': info.get('longName', row.get('Company', ticker)),
            'Current Price': round(current_price, 2),
            'Prev Close': round(prev_price, 2),
            'Change (%)': round(((current_price - prev_price) / prev_price * 100), 2),
            'Target (+₹20)': round(target_20rs, 2),
            'Target (+3%)': round(target_3pct, 2),
            '% to ₹20 Target': round(percent_change_20rs, 2),
            'Probability Score': round(prob_score, 1),
            'RSI': round(indicators['rsi'], 2),
            'Volume Ratio': round(indicators['volume_ratio'], 2),
            '5D Momentum (%)': round(indicators['price_change_5d'], 2),
            '20D Momentum (%)': round(indicators['price_change_20d'], 2),
            'Volatility (%)': round(indicators['volatility'], 2),
            'Sector': info.get('sector', 'N/A'),
            'Market Cap': info.get('marketCap', 0)
        }
    except Exception as e:
        return None

def get_detailed_stock_info(ticker):
    """Get detailed information for a specific stock"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period='1y')
        
        # Financial ratios
        financials = {
            'P/E Ratio': info.get('trailingPE', 'N/A'),
            'Forward P/E': info.get('forwardPE', 'N/A'),
            'P/B Ratio': info.get('priceToBook', 'N/A'),
            'Debt to Equity': info.get('debtToEquity', 'N/A'),
            'ROE (%)': info.get('returnOnEquity', 'N/A'),
            'ROA (%)': info.get('returnOnAssets', 'N/A'),
            'Profit Margin (%)': info.get('profitMargins', 'N/A'),
            'Operating Margin (%)': info.get('operatingMargins', 'N/A'),
            'Revenue Growth (%)': info.get('revenueGrowth', 'N/A'),
            'Earnings Growth (%)': info.get('earningsGrowth', 'N/A'),
            'Current Ratio': info.get('currentRatio', 'N/A'),
            'Quick Ratio': info.get('quickRatio', 'N/A'),
            'Dividend Yield (%)': info.get('dividendYield', 'N/A'),
            'Payout Ratio (%)': info.get('payoutRatio', 'N/A'),
        }
        
        # Format the values
        for key, value in financials.items():
            if isinstance(value, (int, float)) and value != 'N/A':
                if 'Margin' in key or 'Growth' in key or 'Yield' in key or 'Ratio' in key or 'ROE' in key or 'ROA' in key:
                    if abs(value) < 1:
                        financials[key] = f"{value * 100:.2f}%"
                    else:
                        financials[key] = f"{value:.2f}"
                else:
                    financials[key] = f"{value:.2f}"
        
        return {
            'info': info,
            'history': hist,
            'financials': financials
        }
    except Exception as e:
        return None

# Main app
st.markdown('<p class="main-header">📈 Indian Stock Analyzer</p>', unsafe_allow_html=True)
st.markdown("### Find stocks with high probability of moving +₹20 or +3%")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # File upload
    st.subheader("📁 Upload Stock List")
    uploaded_file = st.file_uploader(
        "Upload CSV with 'Ticker' and 'Company' columns",
        type=['csv'],
        help="CSV should have columns: Ticker (e.g., RELIANCE, TCS) and Company (optional)"
    )
    
    if uploaded_file is not None:
        st.session_state.uploaded_df = pd.read_csv(uploaded_file)
        st.success(f"✅ Loaded {len(st.session_state.uploaded_df)} stocks")
    
    # Sample data option
    if st.button("📊 Use Sample Stocks (Top 50 NSE)"):
        sample_tickers = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC', 'SBIN', 
            'BHARTIARTL', 'KOTAKBANK', 'LT', 'BAJFINANCE', 'ASIANPAINT', 'HCLTECH', 'AXISBANK',
            'MARUTI', 'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'WIPRO', 'ONGC', 
            'NTPC', 'POWERGRID', 'TATAMOTORS', 'TECHM', 'BAJAJFINSV', 'M&M', 'COALINDIA',
            'ADANIPORTS', 'TATASTEEL', 'HINDALCO', 'JSWSTEEL', 'INDUSINDBK', 'GRASIM',
            'DRREDDY', 'CIPLA', 'BRITANNIA', 'DIVISLAB', 'EICHERMOT', 'SHREECEM', 'HEROMOTOCO',
            'APOLLOHOSP', 'BAJAJ-AUTO', 'SBILIFE', 'HDFCLIFE', 'ADANIENT', 'VEDL', 'BPCL', 'IOC'
        ]
        st.session_state.uploaded_df = pd.DataFrame({'Ticker': sample_tickers})
        st.success(f"✅ Loaded {len(sample_tickers)} sample stocks")
    
    st.divider()
    
    # Analysis settings
    st.subheader("🎯 Analysis Settings")
    min_prob_score = st.slider("Minimum Probability Score", 0, 100, 50, 5)
    max_stocks_to_show = st.slider("Max Stocks to Display", 10, 100, 50, 10)
    
    st.divider()
    st.markdown("### 📖 How It Works")
    st.markdown("""
    1. **Upload** your stock list or use sample data
    2. **Analyze** - We fetch real-time data and calculate probability scores
    3. **Review** - See stocks ranked by movement probability
    4. **Deep Dive** - Click any stock for detailed analysis
    """)

# Main content
tab1, tab2 = st.tabs(["🔍 Stock Scanner", "📊 Detailed Analysis"])

with tab1:
    if st.session_state.uploaded_df is not None:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Stocks", len(st.session_state.uploaded_df))
        
        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            total = len(st.session_state.uploaded_df)
            
            # Analyze stocks with progress tracking
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(analyze_single_stock, row): idx 
                          for idx, row in st.session_state.uploaded_df.iterrows()}
                
                for i, future in enumerate(as_completed(futures)):
                    progress = (i + 1) / total
                    progress_bar.progress(progress)
                    status_text.text(f"Analyzing stocks... {i+1}/{total}")
                    
                    result = future.result()
                    if result is not None:
                        results.append(result)
                    
                    time.sleep(0.1)  # Rate limiting
            
            progress_bar.empty()
            status_text.empty()
            
            if results:
                df_results = pd.DataFrame(results)
                df_results = df_results[df_results['Probability Score'] >= min_prob_score]
                df_results = df_results.sort_values('Probability Score', ascending=False).head(max_stocks_to_show)
                st.session_state.analyzed_stocks = df_results
                
                st.success(f"✅ Analysis complete! Found {len(df_results)} potential stocks")
            else:
                st.warning("No stocks met the criteria. Try adjusting the minimum probability score.")
        
        # Display results
        if st.session_state.analyzed_stocks is not None and not st.session_state.analyzed_stocks.empty:
            st.divider()
            st.subheader("📈 High Probability Stocks")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            df = st.session_state.analyzed_stocks
            
            with col1:
                st.metric("Stocks Found", len(df))
            with col2:
                avg_prob = df['Probability Score'].mean()
                st.metric("Avg Probability", f"{avg_prob:.1f}%")
            with col3:
                avg_target = df['% to ₹20 Target'].mean()
                st.metric("Avg % to Target", f"{avg_target:.1f}%")
            with col4:
                strong_stocks = len(df[df['Probability Score'] >= 70])
                st.metric("Strong Signals", strong_stocks)
            
            # Display table
            display_cols = ['Ticker', 'Company', 'Current Price', 'Change (%)', 
                          'Target (+₹20)', '% to ₹20 Target', 'Probability Score', 
                          'RSI', 'Volume Ratio', '5D Momentum (%)', 'Sector']
            
            st.dataframe(
                df[display_cols].style.background_gradient(
                    subset=['Probability Score'], cmap='RdYlGn', vmin=0, vmax=100
                ).format({
                    'Current Price': '₹{:.2f}',
                    'Target (+₹20)': '₹{:.2f}',
                    'Change (%)': '{:.2f}%',
                    '% to ₹20 Target': '{:.2f}%',
                    'Probability Score': '{:.1f}',
                    'RSI': '{:.1f}',
                    'Volume Ratio': '{:.2f}x',
                    '5D Momentum (%)': '{:.2f}%'
                }),
                use_container_width=True,
                height=400
            )
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download Results (CSV)",
                csv,
                "stock_analysis_results.csv",
                "text/csv",
                use_container_width=True
            )
    else:
        st.info("👆 Please upload a stock list or use sample data from the sidebar to begin")

with tab2:
    st.subheader("🔬 Detailed Stock Analysis")
    
    if st.session_state.analyzed_stocks is not None and not st.session_state.analyzed_stocks.empty:
        selected_ticker = st.selectbox(
            "Select a stock for detailed analysis:",
            st.session_state.analyzed_stocks['Ticker'].tolist()
        )
        
        if selected_ticker:
            with st.spinner("Loading detailed information..."):
                details = get_detailed_stock_info(selected_ticker)
                
                if details:
                    info = details['info']
                    hist = details['history']
                    financials = details['financials']
                    
                    # Company header
                    st.markdown(f"## {info.get('longName', selected_ticker)}")
                    st.markdown(f"**Sector:** {info.get('sector', 'N/A')} | **Industry:** {info.get('industry', 'N/A')}")
                    st.markdown(f"**Website:** {info.get('website', 'N/A')}")
                    
                    # Key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        current = hist['Close'].iloc[-1]
                        st.metric("Current Price", f"₹{current:.2f}")
                    with col2:
                        change = ((current - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100)
                        st.metric("Daily Change", f"{change:.2f}%", delta=f"{change:.2f}%")
                    with col3:
                        market_cap = info.get('marketCap', 0)
                        if market_cap > 0:
                            st.metric("Market Cap", f"₹{market_cap/10000000:.2f}Cr")
                        else:
                            st.metric("Market Cap", "N/A")
                    with col4:
                        pe = info.get('trailingPE', 'N/A')
                        st.metric("P/E Ratio", f"{pe:.2f}" if isinstance(pe, (int, float)) else "N/A")
                    
                    # Price chart
                    st.subheader("📊 Price Chart (1 Year)")
                    chart_data = pd.DataFrame({
                        'Date': hist.index,
                        'Price': hist['Close'].values
                    }).set_index('Date')
                    st.line_chart(chart_data, height=300)
                    
                    # Financial ratios
                    st.subheader("💼 Key Financial Ratios")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Valuation Metrics**")
                        for key in ['P/E Ratio', 'Forward P/E', 'P/B Ratio', 'Dividend Yield (%)']:
                            st.text(f"{key}: {financials.get(key, 'N/A')}")
                        
                        st.markdown("**Profitability Metrics**")
                        for key in ['ROE (%)', 'ROA (%)', 'Profit Margin (%)', 'Operating Margin (%)']:
                            st.text(f"{key}: {financials.get(key, 'N/A')}")
                    
                    with col2:
                        st.markdown("**Growth Metrics**")
                        for key in ['Revenue Growth (%)', 'Earnings Growth (%)']:
                            st.text(f"{key}: {financials.get(key, 'N/A')}")
                        
                        st.markdown("**Liquidity & Leverage**")
                        for key in ['Current Ratio', 'Quick Ratio', 'Debt to Equity']:
                            st.text(f"{key}: {financials.get(key, 'N/A')}")
                    
                    # Company description
                    if 'longBusinessSummary' in info:
                        st.subheader("📝 Company Overview")
                        st.write(info['longBusinessSummary'])
                    
                else:
                    st.error("Unable to fetch detailed information for this stock")
    else:
        st.info("Run the analysis in the 'Stock Scanner' tab first to see detailed information")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Disclaimer:</strong> This tool is for educational purposes only. Not financial advice. 
    Always do your own research and consult with a qualified financial advisor before making investment decisions.</p>
    <p>Data source: Yahoo Finance | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)