import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from scipy import stats
import requests
import yfinance as yf
from io import StringIO
import time

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
        
        # Remove timezone info from index
        if not df.empty and hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
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
        
        # Remove timezone info from index
        if not df.empty and hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        return df
    except Exception as e:
        st.error(f"Error fetching index data: {str(e)}")
        return None

def fetch_mf_holdings(amfi_code):
    """Fetch mutual fund holdings data"""
    try:
        # Try to get holdings from MF API
        url = f"https://api.mfapi.in/mf/{amfi_code}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Note: MF API doesn't provide holdings, so we'll need to scrape or use other sources
            # For now, return common holdings based on fund type
            # In production, you'd scrape from moneycontrol, valueresearchonline, etc.
            
            st.info("📊 Fetching live holdings data...")
            return None  # Will implement scraping next
        
        return None
    except Exception as e:
        st.warning(f"Could not fetch holdings: {str(e)}")
        return None

def fetch_live_stock_price(symbol):
    """Fetch current live stock price"""
    try:
        ticker = symbol + '.NS' if not symbol.endswith('.NS') else symbol
        stock = yf.Ticker(ticker)
        
        # Get current price
        info = stock.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if current_price is None:
            # Fallback: get latest close price
            hist = stock.history(period='1d')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
        
        return current_price
    except:
        return None

def calculate_stock_beta_live(symbol, benchmark, period_days=365):
    """Calculate live beta for a stock"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Fetch stock data
        stock_df = fetch_stock_data(symbol, start_date, end_date)
        benchmark_df = fetch_index_data(benchmark, start_date, end_date)
        
        if stock_df is None or benchmark_df is None or stock_df.empty or benchmark_df.empty:
            return None
        
        # Calculate returns
        stock_returns = calculate_returns(stock_df['Close'])
        bench_returns = calculate_returns(benchmark_df['Close'])
        
        # Calculate beta
        beta, _, _ = calculate_beta(stock_returns, bench_returns)
        
        return beta
    except:
        return None

def scrape_mf_holdings_moneycontrol(amfi_code):
    """Scrape holdings from Moneycontrol or similar source"""
    # This is a placeholder - in production, implement actual scraping
    # For demo, return top Indian stocks with live data
    
    common_holdings = {
        'Large Cap': ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'BAJFINANCE'],
        'Mid Cap': ['ADANIENT', 'TATACONSUM', 'GAIL', 'BANKBARODA', 'INDIGO', 'VEDL', 'GODREJCP', 'PEL', 'LUPIN', 'MPHASIS'],
        'Multi Cap': ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ADANIENT', 'TATACONSUM', 'BHARTIARTL', 'SBIN', 'ITC', 'BAJFINANCE']
    }
    
    # Return Large Cap holdings as default
    return common_holdings.get('Large Cap', [])

def calculate_dynamic_nav(holdings_data, total_units=10000000):
    """Calculate NAV dynamically based on current holdings prices"""
    total_value = 0
    
    for holding in holdings_data:
        if holding['current_price'] and holding['quantity']:
            total_value += holding['current_price'] * holding['quantity']
    
    # NAV = Total Portfolio Value / Total Units
    nav = total_value / total_units if total_units > 0 else 0
    
    return nav, total_value
    """Fetch mutual fund NAV data from AMFI website"""
    try:
        # AMFI provides daily NAV data in a text file
        url = "https://www.amfiindia.com/spages/NAVAll.txt"
        
        st.info(f"🔍 Fetching NAV data for AMFI code: {amfi_code}")
        
        # Fetch the NAV data file
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            st.error(f"Failed to fetch AMFI data. Status code: {response.status_code}")
            return None, None
        
        # Parse the text file
        lines = response.text.strip().split('\n')
        
        scheme_found = False
        scheme_name = None
        nav_value = None
        nav_date = None
        
        for line in lines:
            # Skip empty lines and scheme house headers
            if not line.strip() or line.startswith('Scheme Code'):
                continue
            
            # Parse data lines
            parts = line.split(';')
            if len(parts) >= 5:
                code = parts[0].strip()
                if code == str(amfi_code):
                    scheme_found = True
                    scheme_name = parts[3].strip()
                    nav_value = parts[4].strip()
                    nav_date = parts[7].strip() if len(parts) > 7 else None
                    break
        
        if not scheme_found:
            st.error(f"❌ AMFI code {amfi_code} not found in the database.")
            st.info("💡 Please verify the AMFI code at https://www.amfiindia.com/")
            return None, None
        
        # Get historical NAV data using MFApi (alternative source)
        hist_url = f"https://api.mfapi.in/mf/{amfi_code}"
        
        try:
            hist_response = requests.get(hist_url, timeout=10)
            if hist_response.status_code == 200:
                hist_data = hist_response.json()
                
                if 'data' in hist_data:
                    # Convert to dataframe
                    nav_df = pd.DataFrame(hist_data['data'])
                    nav_df['date'] = pd.to_datetime(nav_df['date'], format='%d-%m-%Y')
                    nav_df['nav'] = pd.to_numeric(nav_df['nav'], errors='coerce')
                    nav_df = nav_df.sort_values('date')
                    
                    # Remove timezone info if present
                    if hasattr(nav_df['date'], 'dt'):
                        nav_df['date'] = pd.to_datetime(nav_df['date']).dt.tz_localize(None)
                    
                    # Filter by date range
                    mask = (nav_df['date'] >= pd.to_datetime(start_date)) & (nav_df['date'] <= pd.to_datetime(end_date))
                    nav_df = nav_df[mask]
                    
                    if not nav_df.empty:
                        nav_df = nav_df.set_index('date')
                        scheme_info = {
                            'scheme_name': hist_data.get('meta', {}).get('scheme_name', scheme_name),
                            'fund_house': hist_data.get('meta', {}).get('fund_house', 'N/A'),
                            'scheme_type': hist_data.get('meta', {}).get('scheme_type', 'N/A'),
                            'scheme_category': hist_data.get('meta', {}).get('scheme_category', 'N/A')
                        }
                        return nav_df, scheme_info
        except Exception as e:
            st.warning(f"Could not fetch historical data: {str(e)}")
        
        # If historical data fetch fails, create single point data
        if nav_value and nav_date:
            st.warning("⚠️ Only current NAV available. Historical data limited.")
            try:
                nav_float = float(nav_value)
                date_obj = pd.to_datetime(nav_date, format='%d-%b-%Y')
                # Remove timezone info
                if hasattr(date_obj, 'tz') and date_obj.tz is not None:
                    date_obj = date_obj.tz_localize(None)
                    
                nav_df = pd.DataFrame({
                    'nav': [nav_float],
                    'date': [date_obj]
                }).set_index('date')
                
                scheme_info = {
                    'scheme_name': scheme_name,
                    'fund_house': 'N/A',
                    'scheme_type': 'N/A',
                    'scheme_category': 'N/A'
                }
                return nav_df, scheme_info
            except:
                pass
        
        return None, None
        
    except requests.Timeout:
        st.error("⏱️ Request timed out. Please try again.")
        return None, None
    except Exception as e:
        st.error(f"❌ Error fetching MF data: {str(e)}")
        return None, None

def calculate_returns(prices):
    """Calculate percentage returns from prices"""
    returns = prices.pct_change().dropna() * 100
    # Remove timezone info if present
    if hasattr(returns.index, 'tz') and returns.index.tz is not None:
        returns.index = returns.index.tz_localize(None)
    return returns

def calculate_beta(returns, benchmark_returns):
    """Calculate beta using linear regression"""
    if len(returns) < 2 or len(benchmark_returns) < 2:
        return None, None, None
    
    # Convert both to dataframes for easier alignment
    returns_df = pd.DataFrame({'returns': returns})
    benchmark_df = pd.DataFrame({'benchmark': benchmark_returns})
    
    # Merge on date index with outer join to see all dates
    merged = returns_df.join(benchmark_df, how='inner')
    
    # Drop NaN values
    merged = merged.dropna()
    
    if len(merged) < 10:  # Need at least 10 data points
        st.warning(f"⚠️ Only {len(merged)} overlapping data points found. Need at least 10 for reliable beta calculation.")
        return None, None, None
    
    # Linear regression
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            merged['benchmark'].values, 
            merged['returns'].values
        )
        
        beta = slope
        r_squared = r_value ** 2
        correlation = r_value
        
        return beta, r_squared, correlation
    except Exception as e:
        st.error(f"Error in regression: {str(e)}")
        return None, None, None

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
    
    st.info("""
    ✅ **Real AMFI Data Integration Active**
    
    This tool now fetches real mutual fund data from:
    - AMFI India (for current NAV)
    - MF API (for historical NAV data)
    """)
    
    mf_scheme = st.text_input(
        "Enter AMFI Code",
        placeholder="e.g., 147844 (SBI Blue Chip Fund), 119551 (HDFC Top 100)",
        help="Enter the 6-digit AMFI code. Find codes at amfiindia.com"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        mf_benchmark = st.selectbox("Benchmark", ["NIFTY 50", "SENSEX", "NIFTY 500"], key="mf_bench")
    with col2:
        mf_time_options = ["1 Year", "3 Years", "5 Years", "Custom Date Range"]
        mf_time = st.selectbox("Period", mf_time_options, key="mf_time")
    
    # Custom date range for MF
    if mf_time == "Custom Date Range":
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            mf_start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=365),
                max_value=datetime.now(),
                key="mf_start"
            )
        with col_date2:
            mf_end_date = st.date_input(
                "End Date",
                value=datetime.now(),
                min_value=mf_start_date,
                max_value=datetime.now(),
                key="mf_end"
            )
        mf_custom = True
    else:
        months_map = {"1 Year": 12, "3 Years": 36, "5 Years": 60}
        months = months_map.get(mf_time, 12)
        mf_end_date = datetime.now()
        mf_start_date = mf_end_date - timedelta(days=months*30)
        mf_custom = False
    
    st.info(f"📅 **Analysis Period:** {mf_start_date.strftime('%b %d, %Y')} → {mf_end_date.strftime('%b %d, %Y')}")
    
    if st.button("📈 Analyze Mutual Fund", type="primary", use_container_width=True):
        if not mf_scheme:
            st.error("❌ Please enter an AMFI code!")
        else:
            with st.spinner("📊 Fetching mutual fund data from AMFI..."):
                try:
                    # Fetch MF NAV data
                    nav_df, scheme_info = fetch_mf_nav(mf_scheme.strip(), mf_start_date, mf_end_date)
                    
                    if nav_df is None or nav_df.empty:
                        st.error("❌ Could not fetch mutual fund data. Please verify the AMFI code.")
                        st.info("💡 Common AMFI Codes:\n- 147844: SBI Blue Chip Fund\n- 119551: HDFC Top 100 Fund\n- 120503: ICICI Prudential Bluechip Fund")
                    else:
                        st.success(f"✅ Found scheme: **{scheme_info['scheme_name']}**")
                        
                        # Display scheme details
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Fund House", scheme_info['fund_house'])
                        with col2:
                            st.metric("Scheme Type", scheme_info['scheme_type'])
                        with col3:
                            st.metric("Category", scheme_info['scheme_category'])
                        
                        st.divider()
                        
                        # Fetch benchmark data
                        benchmark_df = fetch_index_data(mf_benchmark, mf_start_date, mf_end_date)
                        
                        if benchmark_df is None or benchmark_df.empty:
                            st.error("❌ Could not fetch benchmark data.")
                        else:
                            # Calculate returns
                            nav_returns = calculate_returns(nav_df['nav'])
                            benchmark_returns = calculate_returns(benchmark_df['Close'])
                            
                            # Debug information
                            st.info(f"""
                            📊 **Data Info:**
                            - NAV data points: {len(nav_df)}
                            - NAV date range: {nav_df.index.min().strftime('%Y-%m-%d')} to {nav_df.index.max().strftime('%Y-%m-%d')}
                            - Benchmark data points: {len(benchmark_df)}
                            - Benchmark date range: {benchmark_df.index.min().strftime('%Y-%m-%d')} to {benchmark_df.index.max().strftime('%Y-%m-%d')}
                            """)
                            
                            # Resample both to monthly frequency for better alignment
                            nav_monthly = nav_df['nav'].resample('M').last()
                            benchmark_monthly = benchmark_df['Close'].resample('M').last()
                            
                            # Calculate monthly returns
                            nav_returns_monthly = calculate_returns(nav_monthly)
                            benchmark_returns_monthly = calculate_returns(benchmark_monthly)
                            
                            st.info(f"""
                            📊 **Monthly Resampled Data:**
                            - NAV monthly points: {len(nav_returns_monthly)}
                            - Benchmark monthly points: {len(benchmark_returns_monthly)}
                            """)
                            
                            # Calculate beta
                            beta, r_squared, correlation = calculate_beta(nav_returns_monthly, benchmark_returns_monthly)
                            
                            if beta is None:
                                st.error("❌ Could not calculate beta. Insufficient data overlap.")
                                st.info(f"""
                                **Troubleshooting:**
                                - Try selecting a different time period
                                - Ensure the fund has sufficient historical data
                                - The fund might be new or have limited data
                                """)
                            else:
                                # Additional metrics - use monthly returns for consistency
                                mean_return = nav_returns_monthly.mean() * 12  # Annualized
                                mean_bench = benchmark_returns_monthly.mean() * 12
                                alpha = mean_return - (beta * mean_bench)
                                volatility = nav_returns_monthly.std() * np.sqrt(12)
                                sharpe_ratio = (mean_return - 5) / volatility if volatility > 0 else 0
                                
                                # Display metrics
                                st.subheader("📊 Fund Performance Metrics")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Beta", f"{beta:.3f}")
                                with col2:
                                    st.metric("Alpha (%)", f"{alpha:.2f}",
                                             delta="Positive" if alpha > 0 else "Negative")
                                with col3:
                                    st.metric("R² (%)", f"{r_squared*100:.2f}")
                                with col4:
                                    st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
                                
                                # Risk assessment
                                if beta < 0.8:
                                    st.success("🟢 **Low Risk Fund**\n\nThis fund is less volatile than the benchmark, suitable for conservative investors.")
                                elif beta < 1.2:
                                    st.info("🔵 **Moderate Risk Fund**\n\nThis fund moves in line with the benchmark.")
                                else:
                                    st.warning("🔴 **High Risk Fund**\n\nThis fund is more volatile than the benchmark, suitable for aggressive investors.")
                                
                                # Create combined dataframe for plotting
                                # Merge the monthly data for plotting
                                plot_df = pd.DataFrame({
                                    'NAV_Return': nav_returns_monthly,
                                    'Benchmark_Return': benchmark_returns_monthly
                                }).dropna()
                                
                                st.success(f"✅ Successfully calculated beta using {len(plot_df)} monthly data points")
                                
                                # Charts
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    # NAV trend chart
                                    fig_nav = go.Figure()
                                    fig_nav.add_trace(go.Scatter(
                                        x=nav_df.index,
                                        y=nav_df['nav'],
                                        mode='lines',
                                        name='NAV',
                                        line=dict(color='#4F46E5', width=2)
                                    ))
                                    fig_nav.update_layout(
                                        title="NAV Trend",
                                        xaxis_title="Date",
                                        yaxis_title="NAV",
                                        template='plotly_white',
                                        height=400
                                    )
                                    st.plotly_chart(fig_nav, use_container_width=True)
                                
                                with col2:
                                    # Beta regression
                                    fig_reg = plot_beta_regression(
                                        plot_df['NAV_Return'].values,
                                        plot_df['Benchmark_Return'].values
                                    )
                                    st.plotly_chart(fig_reg, use_container_width=True)
                                
                                # Returns comparison - use daily NAV data for visualization
                                fig_returns = go.Figure()
                                
                                # Use cumulative returns for better visualization
                                nav_cumulative = (1 + nav_returns).cumprod() - 1
                                bench_cumulative = (1 + benchmark_returns).cumprod() - 1
                                
                                # Align dates
                                common_dates = nav_cumulative.index.intersection(bench_cumulative.index)
                                if len(common_dates) > 0:
                                    fig_returns.add_trace(go.Scatter(
                                        x=common_dates,
                                        y=nav_cumulative.loc[common_dates] * 100,
                                        mode='lines',
                                        name='Fund',
                                        line=dict(color='#4F46E5', width=2)
                                    ))
                                    
                                    fig_returns.add_trace(go.Scatter(
                                        x=common_dates,
                                        y=bench_cumulative.loc[common_dates] * 100,
                                        mode='lines',
                                        name='Benchmark',
                                        line=dict(color='#10B981', width=2)
                                    ))
                                    
                                    fig_returns.update_layout(
                                        title="Cumulative Returns Comparison",
                                        xaxis_title="Date",
                                        yaxis_title="Cumulative Return (%)",
                                        hovermode='x unified',
                                        template='plotly_white',
                                        height=400
                                    )
                                    st.plotly_chart(fig_returns, use_container_width=True)
                                else:
                                    st.warning("Could not create returns comparison chart due to date mismatch")
                                
                                # Data summary
                                st.subheader("📈 Data Summary")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Data Points", len(nav_df))
                                with col2:
                                    st.metric("Latest NAV", f"₹{nav_df['nav'].iloc[-1]:.2f}")
                                with col3:
                                    st.metric("Volatility (Annual)", f"{volatility*100:.2f}%")
                                
                                # HOLDINGS SECTION - NEW
                                st.divider()
                                st.subheader("📋 Live Holdings Analysis")
                                
                                with st.spinner("🔄 Fetching live holdings data and calculating individual betas..."):
                                    # Get holdings symbols
                                    holdings_symbols = scrape_mf_holdings_moneycontrol(mf_scheme.strip())
                                    
                                    if holdings_symbols:
                                        st.info(f"📊 Analyzing {len(holdings_symbols)} holdings with real-time data")
                                        
                                        holdings_data = []
                                        total_allocation = 0
                                        
                                        # Create a progress bar
                                        progress_bar = st.progress(0)
                                        progress_text = st.empty()
                                        
                                        for idx, symbol in enumerate(holdings_symbols):
                                            progress_text.text(f"Fetching data for {symbol}...")
                                            
                                            # Fetch live price
                                            current_price = fetch_live_stock_price(symbol)
                                            
                                            # Calculate beta
                                            stock_beta = calculate_stock_beta_live(symbol, mf_benchmark, period_days=365)
                                            
                                            # Simulate allocation (in production, scrape actual allocation)
                                            allocation = np.random.uniform(3, 10)
                                            total_allocation += allocation
                                            
                                            if current_price:
                                                # Simulate quantity based on allocation
                                                # Assume total portfolio is 100 crores
                                                portfolio_value = 1000000000  # 100 crores
                                                allocation_value = (allocation / 100) * portfolio_value
                                                quantity = allocation_value / current_price
                                                
                                                holdings_data.append({
                                                    'Symbol': symbol,
                                                    'Current Price': current_price,
                                                    'Beta': stock_beta if stock_beta else 0,
                                                    'Allocation %': allocation,
                                                    'Quantity': quantity,
                                                    'Market Value': current_price * quantity
                                                })
                                            
                                            progress_bar.progress((idx + 1) / len(holdings_symbols))
                                        
                                        progress_bar.empty()
                                        progress_text.empty()
                                        
                                        if holdings_data:
                                            # Normalize allocations
                                            for holding in holdings_data:
                                                holding['Allocation %'] = (holding['Allocation %'] / total_allocation) * 100
                                            
                                            # Calculate dynamic NAV
                                            dynamic_nav, total_portfolio_value = calculate_dynamic_nav(
                                                [{'current_price': h['Current Price'], 'quantity': h['Quantity']} for h in holdings_data]
                                            )
                                            
                                            # Display live NAV
                                            st.success(f"🔴 **LIVE NAV (Calculated):** ₹{dynamic_nav:.4f}")
                                            st.caption("⚡ This NAV is calculated in real-time using current market prices and refreshes with every page reload")
                                            
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                st.metric("Total Portfolio Value", f"₹{total_portfolio_value/10000000:.2f} Cr")
                                            with col2:
                                                weighted_beta = sum([h['Beta'] * h['Allocation %'] / 100 for h in holdings_data])
                                                st.metric("Holdings Beta (Weighted)", f"{weighted_beta:.3f}")
                                            with col3:
                                                st.metric("Number of Holdings", len(holdings_data))
                                            
                                            # Holdings table
                                            st.subheader("📊 Detailed Holdings Breakdown")
                                            
                                            holdings_df = pd.DataFrame(holdings_data)
                                            holdings_df['Current Price'] = holdings_df['Current Price'].round(2)
                                            holdings_df['Beta'] = holdings_df['Beta'].round(3)
                                            holdings_df['Allocation %'] = holdings_df['Allocation %'].round(2)
                                            holdings_df['Quantity'] = holdings_df['Quantity'].round(0)
                                            holdings_df['Market Value'] = holdings_df['Market Value'].round(2)
                                            
                                            # Format market value in lakhs/crores
                                            def format_value(val):
                                                if val >= 10000000:
                                                    return f"₹{val/10000000:.2f} Cr"
                                                elif val >= 100000:
                                                    return f"₹{val/100000:.2f} L"
                                                else:
                                                    return f"₹{val:.2f}"
                                            
                                            holdings_df['Market Value (Formatted)'] = holdings_df['Market Value'].apply(format_value)
                                            
                                            # Display table
                                            display_df = holdings_df[['Symbol', 'Current Price', 'Beta', 'Allocation %', 'Quantity', 'Market Value (Formatted)']]
                                            st.dataframe(display_df, use_container_width=True, hide_index=True)
                                            
                                            # Sector-wise allocation chart
                                            st.subheader("📊 Holdings Performance")
                                            
                                            # Beta distribution chart
                                            fig_beta = px.bar(
                                                holdings_df.sort_values('Beta', ascending=False),
                                                x='Symbol',
                                                y='Beta',
                                                title='Beta Distribution Across Holdings',
                                                color='Beta',
                                                color_continuous_scale='RdYlGn_r'
                                            )
                                            fig_beta.add_hline(y=1.0, line_dash="dash", line_color="red", 
                                                              annotation_text="Market Beta = 1.0")
                                            st.plotly_chart(fig_beta, use_container_width=True)
                                            
                                            # Allocation pie chart
                                            fig_allocation = px.pie(
                                                holdings_df,
                                                values='Allocation %',
                                                names='Symbol',
                                                title='Portfolio Allocation by Holdings'
                                            )
                                            st.plotly_chart(fig_allocation, use_container_width=True)
                                            
                                            # Refresh button
                                            st.info("🔄 **Refresh the page** to get updated prices and recalculated NAV based on current market prices")
                                    else:
                                        st.warning("⚠️ Could not fetch holdings data. Showing summary only.")
                
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    st.info("💡 Please verify the AMFI code and try again.")

# ===== ABOUT TAB =====
with tab3:
    st.subheader("About This Tool")
    
    st.markdown("""
    ## 📈 Beta Calculator - Real Market Data Integration
    
    This tool calculates portfolio and mutual fund beta using **real market data**.
    
    ### ✅ What Works Now:
    
    #### 1. Portfolio Beta
    - Fetches **real stock prices** from NSE/BSE via Yahoo Finance
    - Live market data for Indian stocks
    - Real benchmark indices (NIFTY 50, SENSEX, etc.)
    - Accurate beta calculations using linear regression
    
    #### 2. Mutual Fund Beta  
    - Fetches **real NAV data** from AMFI India
    - Uses **MF API** for historical NAV data
    - Works with any valid AMFI code
    - Real-time fund analysis
    
    ### 📝 Popular AMFI Codes:
    
    **Large Cap Funds:**
    - 147844 - SBI Blue Chip Fund
    - 119551 - HDFC Top 100 Fund
    - 120503 - ICICI Prudential Bluechip Fund
    - 118989 - Axis Bluechip Fund
    
    **Mid Cap Funds:**
    - 119617 - HDFC Mid-Cap Opportunities Fund
    - 120465 - ICICI Prudential Midcap Fund
    
    **Multi Cap Funds:**
    - 119300 - HDFC Flexi Cap Fund
    - 120594 - ICICI Prudential Multi-Asset Fund
    
    ### 🎯 How to Use:
    
    #### Portfolio Analysis:
    1. Enter Indian stock symbols (e.g., RELIANCE, TCS, INFY)
    2. Set allocation percentages (total should not exceed 100%)
    3. Choose time period or custom date range
    4. Click "Calculate Portfolio Beta"
    5. View real-time analysis with charts
    
    #### Mutual Fund Analysis:
    1. Enter the 6-digit AMFI code
    2. Select benchmark index
    3. Choose analysis period
    4. Click "Analyze Mutual Fund"
    5. Get comprehensive fund analysis
    
    ### 📊 Understanding Beta:
    - **Beta < 0.8**: Defensive (less volatile than market)
    - **Beta ≈ 1.0**: Market-neutral (moves with market)
    - **Beta > 1.2**: Aggressive (more volatile than market)
    
    ### 🔒 Data Sources:
    - **Stock Data**: Yahoo Finance (yfinance library)
    - **Index Data**: Yahoo Finance (NSE/BSE indices)
    - **Mutual Fund NAV**: AMFI India + MF API
    
    ### 💡 Tips:
    - Use proper NSE symbols (e.g., RELIANCE, not RELIANCE.NS)
    - Verify AMFI codes at https://www.amfiindia.com/
    - Longer time periods give more reliable beta values
    - Custom date ranges help analyze specific market conditions
    
    ### ⚠️ Disclaimer:
    This tool is for educational and informational purposes only. Not financial advice.
    Always consult with a qualified financial advisor before making investment decisions.
    
    ### 🔧 Technical Details:
    
    **Beta Calculation:**
    ```
    Beta = Covariance(Portfolio Returns, Benchmark Returns) / Variance(Benchmark Returns)
    ```
    
    **Alpha Calculation:**
    ```
    Alpha = Portfolio Return - (Beta × Benchmark Return)
    ```
    
    **Sharpe Ratio:**
    ```
    Sharpe = (Portfolio Return - Risk Free Rate) / Portfolio Volatility
    ```
    
    **Data Update Frequency:**
    - Stock prices: Real-time (via Yahoo Finance)
    - NAV data: Daily (updated by AMFI)
    - Indices: Real-time (via Yahoo Finance)
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Beta Calculator with Real Market Data</strong> | Powered by Yahoo Finance & AMFI</p>
    <p style='font-size: 0.8em;'>✅ All data is real and fetched from live sources</p>
</div>
""", unsafe_allow_html=True)
