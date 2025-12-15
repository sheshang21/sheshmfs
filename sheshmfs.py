import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from scipy import stats
import requests
import yfinance as yf

# Page configuration
st.set_page_config(
    page_title="Portfolio & MF Beta Calculator",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None

# Title
st.title("📈 Portfolio & Mutual Fund Beta Calculator")
st.markdown("**Real-time Risk Analysis with Live Market Data**")
st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Portfolio Beta", "💼 Mutual Fund Beta", "ℹ️ About"])

def fetch_stock_data(symbol, start_date, end_date):
    """Fetch real stock data from Yahoo Finance"""
    try:
        # Add .NS for NSE stocks if not present
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            ticker = symbol + '.NS'
        else:
            ticker = symbol
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            # Try BSE
            ticker = symbol.replace('.NS', '.BO')
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
        
        return df
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

def fetch_index_data(index_name, start_date, end_date):
    """Fetch benchmark index data"""
    index_map = {
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "NIFTY 500": "^CRSLDX",
        "NIFTY Midcap 100": "^NSEMDCP50"
    }
    
    ticker = index_map.get(index_name, "^NSEI")
    
    try:
        index = yf.Ticker(ticker)
        df = index.history(start=start_date, end=end_date)
        return df
    except Exception as e:
        st.error(f"Error fetching index data: {str(e)}")
        return None

def fetch_mf_nav(amfi_code, start_date, end_date):
    """Fetch mutual fund NAV data from AMFI or MFCentral"""
    try:
        # This is a placeholder - you need to implement actual API integration
        # Options:
        # 1. MFCentral API (requires registration)
        # 2. AMFI India website scraping
        # 3. RapidAPI mutual fund APIs
        # 4. BSE/NSE APIs for ETFs
        
        st.warning("⚠️ Real-time MF data fetching requires API integration. Please see the About tab for setup instructions.")
        return None
    except Exception as e:
        st.error(f"Error fetching MF data: {str(e)}")
        return None

def calculate_returns(prices):
    """Calculate percentage returns from prices"""
    returns = prices.pct_change().dropna() * 100
    return returns

def calculate_beta(returns, benchmark_returns):
    """Calculate beta using linear regression"""
    if len(returns) < 2 or len(benchmark_returns) < 2:
        return None, None, None
    
    # Align the data
    common_index = returns.index.intersection(benchmark_returns.index)
    returns_aligned = returns.loc[common_index]
    benchmark_aligned = benchmark_returns.loc[common_index]
    
    if len(returns_aligned) < 2:
        return None, None, None
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        benchmark_aligned.values, 
        returns_aligned.values
    )
    
    beta = slope
    r_squared = r_value ** 2
    correlation = r_value
    
    return beta, r_squared, correlation

def plot_returns_comparison(df, portfolio_col, benchmark_col):
    """Plot portfolio vs benchmark returns"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df[portfolio_col],
        mode='lines+markers',
        name='Portfolio',
        line=dict(color='#4F46E5', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df[benchmark_col],
        mode='lines+markers',
        name='Benchmark',
        line=dict(color='#10B981', width=2)
    ))
    
    fig.update_layout(
        title="Returns Comparison",
        xaxis_title="Date",
        yaxis_title="Return (%)",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig

def plot_beta_regression(returns, benchmark_returns):
    """Plot scatter plot with regression line"""
    fig = go.Figure()
    
    # Scatter plot
    fig.add_trace(go.Scatter(
        x=benchmark_returns,
        y=returns,
        mode='markers',
        name='Returns',
        marker=dict(size=8, color='#4F46E5', opacity=0.6)
    ))
    
    # Regression line
    slope, intercept, _, _, _ = stats.linregress(benchmark_returns, returns)
    line_x = np.array([min(benchmark_returns), max(benchmark_returns)])
    line_y = slope * line_x + intercept
    
    fig.add_trace(go.Scatter(
        x=line_x,
        y=line_y,
        mode='lines',
        name=f'Regression (β={slope:.3f})',
        line=dict(color='#EF4444', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="Beta Regression Analysis",
        xaxis_title="Benchmark Return (%)",
        yaxis_title="Portfolio Return (%)",
        hovermode='closest',
        template='plotly_white',
        height=400
    )
    
    return fig

# ===== PORTFOLIO BETA TAB =====
with tab1:
    st.subheader("Portfolio Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        benchmark = st.selectbox(
            "Benchmark Index",
            ["NIFTY 50", "SENSEX", "NIFTY 500", "NIFTY Midcap 100"],
            key="portfolio_benchmark"
        )
    
    with col2:
        time_options = ["6 Months", "1 Year", "3 Years", "5 Years", "Custom Date Range"]
        time_period = st.selectbox("Time Period", time_options)
    
    # Custom date range
    if time_period == "Custom Date Range":
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=365),
                max_value=datetime.now()
            )
        with col_date2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now(),
                min_value=start_date,
                max_value=datetime.now()
            )
    else:
        months_map = {
            "6 Months": 6,
            "1 Year": 12,
            "3 Years": 36,
            "5 Years": 60
        }
        months = months_map.get(time_period, 12)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)
    
    st.info(f"📅 **Analysis Period:** {start_date.strftime('%b %d, %Y')} → {end_date.strftime('%b %d, %Y')}")
    
    st.divider()
    
    # Portfolio stocks input
    st.subheader("Portfolio Holdings")
    st.markdown("**Enter Indian stock symbols (NSE/BSE)**")
    st.caption("Examples: RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK")
    
    num_stocks = st.number_input("Number of stocks", min_value=1, max_value=20, value=3)
    
    stocks_data = []
    for i in range(num_stocks):
        col1, col2 = st.columns([3, 1])
        with col1:
            symbol = st.text_input(
                f"Stock {i+1} Symbol", 
                key=f"stock_{i}", 
                placeholder="e.g., RELIANCE, TCS",
                help="Enter NSE symbol without .NS extension"
            )
        with col2:
            allocation = st.number_input(
                f"Allocation %", 
                min_value=0.0, 
                max_value=100.0, 
                value=0.0, 
                key=f"alloc_{i}"
            )
        
        if symbol and allocation > 0:
            stocks_data.append({"Symbol": symbol.upper().strip(), "Allocation": allocation})
    
    # Calculate button
    if st.button("🔍 Calculate Portfolio Beta", type="primary", use_container_width=True):
        if not stocks_data:
            st.error("❌ Please add at least one stock with allocation!")
        elif sum([s["Allocation"] for s in stocks_data]) > 100:
            st.error("❌ Total allocation cannot exceed 100%!")
        else:
            with st.spinner("📊 Fetching real market data and calculating metrics..."):
                try:
                    # Fetch benchmark data
                    benchmark_df = fetch_index_data(benchmark, start_date, end_date)
                    
                    if benchmark_df is None or benchmark_df.empty:
                        st.error("❌ Could not fetch benchmark data. Please check your internet connection.")
                    else:
                        benchmark_returns = calculate_returns(benchmark_df['Close'])
                        
                        # Fetch individual stock data
                        stock_betas = []
                        all_stock_returns = []
                        valid_stocks = []
                        
                        progress_bar = st.progress(0)
                        for idx, stock in enumerate(stocks_data):
                            stock_df = fetch_stock_data(stock['Symbol'], start_date, end_date)
                            
                            if stock_df is not None and not stock_df.empty:
                                stock_returns = calculate_returns(stock_df['Close'])
                                
                                # Calculate individual stock beta
                                stock_beta, _, _ = calculate_beta(stock_returns, benchmark_returns)
                                
                                if stock_beta is not None:
                                    contribution = stock_beta * (stock['Allocation'] / 100)
                                    stock_betas.append({
                                        'Symbol': stock['Symbol'],
                                        'Allocation': stock['Allocation'],
                                        'Beta': stock_beta,
                                        'Contribution': contribution
                                    })
                                    
                                    # Weight the returns
                                    weighted_returns = stock_returns * (stock['Allocation'] / 100)
                                    all_stock_returns.append(weighted_returns)
                                    valid_stocks.append(stock)
                            else:
                                st.warning(f"⚠️ Could not fetch data for {stock['Symbol']}")
                            
                            progress_bar.progress((idx + 1) / len(stocks_data))
                        
                        progress_bar.empty()
                        
                        if not all_stock_returns:
                            st.error("❌ Could not fetch data for any stocks. Please check symbols.")
                        else:
                            # Calculate portfolio returns
                            portfolio_returns_df = pd.concat(all_stock_returns, axis=1)
                            portfolio_returns = portfolio_returns_df.sum(axis=1)
                            
                            # Calculate portfolio beta
                            beta, r_squared, correlation = calculate_beta(
                                portfolio_returns, 
                                benchmark_returns
                            )
                            
                            if beta is None:
                                st.error("❌ Could not calculate beta. Insufficient data overlap.")
                            else:
                                # Calculate additional metrics
                                mean_return = portfolio_returns.mean() * 252  # Annualized (trading days)
                                mean_bench = benchmark_returns.mean() * 252
                                alpha = mean_return - (beta * mean_bench)
                                volatility = portfolio_returns.std() * np.sqrt(252)
                                sharpe_ratio = (mean_return - 5) / volatility if volatility > 0 else 0
                                
                                # Display results
                                st.divider()
                                st.success("✅ Analysis Complete!")
                                
                                # Key metrics
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric("Portfolio Beta", f"{beta:.3f}")
                                with col2:
                                    st.metric("Alpha (%)", f"{alpha:.2f}", 
                                             delta="Positive" if alpha > 0 else "Negative")
                                with col3:
                                    st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
                                with col4:
                                    st.metric("R² (%)", f"{r_squared*100:.2f}")
                                
                                # Risk assessment
                                if beta < 0.8:
                                    st.success("🟢 **Low Risk - Defensive Portfolio**\n\nYour portfolio is less volatile than the market.")
                                elif beta < 1.2:
                                    st.info("🔵 **Moderate Risk - Market-aligned**\n\nYour portfolio moves in line with the benchmark.")
                                else:
                                    st.warning("🔴 **High Risk - Aggressive Portfolio**\n\nYour portfolio is more volatile than the market.")
                                
                                # Create combined dataframe for plotting
                                plot_df = pd.DataFrame({
                                    'Portfolio': portfolio_returns,
                                    'Benchmark': benchmark_returns
                                }).dropna()
                                
                                # Charts
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    fig1 = plot_returns_comparison(plot_df, 'Portfolio', 'Benchmark')
                                    st.plotly_chart(fig1, use_container_width=True)
                                
                                with col2:
                                    fig2 = plot_beta_regression(
                                        plot_df['Portfolio'].values,
                                        plot_df['Benchmark'].values
                                    )
                                    st.plotly_chart(fig2, use_container_width=True)
                                
                                # Stock betas table
                                if stock_betas:
                                    st.subheader("Individual Stock Analysis")
                                    stock_df = pd.DataFrame(stock_betas)
                                    stock_df['Beta'] = stock_df['Beta'].round(3)
                                    stock_df['Contribution'] = stock_df['Contribution'].round(3)
                                    stock_df['Allocation'] = stock_df['Allocation'].round(2)
                                    
                                    st.dataframe(stock_df, use_container_width=True, hide_index=True)
                
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    st.info("💡 Make sure you have internet connection and entered valid stock symbols.")

# ===== MUTUAL FUND BETA TAB =====
with tab2:
    st.subheader("Mutual Fund Beta Analysis")
    
    st.warning("""
    ⚠️ **Real-time Mutual Fund Data Integration Required**
    
    To fetch real mutual fund data, you need to integrate one of these services:
    
    1. **MFCentral API** (Recommended for Indian MFs)
    2. **AMFI India Website** (Web scraping)
    3. **RapidAPI Mutual Fund APIs** (Paid service)
    4. **BSE/NSE APIs** (For ETFs)
    
    Please see the "About" tab for detailed setup instructions.
    """)
    
    mf_scheme = st.text_input(
        "Enter AMFI Code or Scheme Name",
        placeholder="e.g., 147844 (SBI Blue Chip Fund)",
        help="Enter the 6-digit AMFI code"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        mf_benchmark = st.selectbox("Benchmark", ["NIFTY 50", "SENSEX", "NIFTY 500"], key="mf_bench")
    with col2:
        mf_time = st.selectbox("Period", ["1 Year", "3 Years", "5 Years"], key="mf_time")
    
    if st.button("📈 Analyze Mutual Fund", type="primary"):
        st.info("🔄 This feature requires API integration. See the About tab for setup instructions.")

# ===== ABOUT TAB =====
with tab3:
    st.subheader("About This Tool")
    
    st.markdown("""
    ## 📈 Beta Calculator - Real Market Data Integration
    
    This tool calculates portfolio and mutual fund beta using **real market data** from Yahoo Finance and other sources.
    
    ### ✅ What Works Now:
    - **Portfolio Beta**: Fetches real stock prices from NSE/BSE via Yahoo Finance
    - **Live market data** for Indian stocks
    - **Real benchmark indices** (NIFTY 50, SENSEX, etc.)
    - **Accurate beta calculations** using linear regression
    
    ### 🔧 Mutual Fund Data Setup:
    
    To enable real-time mutual fund data, you need to integrate an API:
    
    #### Option 1: MFCentral API (Recommended)
    ```python
    # Register at https://mfcentral.com/
    # Get API credentials
    # Add to your code:
    
    import requests
    
    def fetch_mf_nav(amfi_code, start_date, end_date):
        url = f"https://api.mfcentral.com/nav/{amfi_code}"
        headers = {"Authorization": "Bearer YOUR_API_KEY"}
        response = requests.get(url, headers=headers)
        return response.json()
    ```
    
    #### Option 2: AMFI Website Scraping
    ```python
    # Scrape from https://www.amfiindia.com/
    # Note: Check terms of service before scraping
    ```
    
    #### Option 3: RapidAPI
    ```python
    # Subscribe to MF APIs on RapidAPI
    # https://rapidapi.com/search/mutual%20fund
    ```
    
    ### 📦 Required Packages:
    ```bash
    pip install streamlit pandas numpy scipy plotly yfinance requests
    ```
    
    ### 🎯 How to Use:
    
    1. **Portfolio Tab**: Enter Indian stock symbols (e.g., RELIANCE, TCS, INFY)
    2. Select allocation percentages
    3. Choose time period or custom date range
    4. Click "Calculate Portfolio Beta"
    5. View real-time analysis with charts
    
    ### 📊 Understanding Beta:
    - **Beta < 0.8**: Defensive (less volatile than market)
    - **Beta ≈ 1.0**: Market-neutral (moves with market)
    - **Beta > 1.2**: Aggressive (more volatile than market)
    
    ### 🔒 Data Sources:
    - **Stock Data**: Yahoo Finance (yfinance library)
    - **Index Data**: Yahoo Finance
    - **Mutual Fund**: Requires API integration (see above)
    
    ### ⚠️ Disclaimer:
    This tool is for educational and informational purposes only. Not financial advice.
    Always consult with a qualified financial advisor before making investment decisions.
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Beta Calculator with Real Market Data</strong> | Powered by Yahoo Finance</p>
    <p style='font-size: 0.8em;'>Stock data is real and updated daily. MF integration requires API setup.</p>
</div>
""", unsafe_allow_html=True)
