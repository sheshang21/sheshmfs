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

# ==================== HELPER FUNCTIONS ====================

def fetch_stock_data(symbol, start_date, end_date):
    """Fetch real stock data from Yahoo Finance"""
    try:
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            ticker = symbol + '.NS'
        else:
            ticker = symbol
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            ticker = symbol.replace('.NS', '.BO')
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
        
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
        
        if not df.empty and hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        return df
    except Exception as e:
        st.error(f"Error fetching index data: {str(e)}")
        return None

def calculate_returns(prices):
    """Calculate percentage returns from prices"""
    returns = prices.pct_change().dropna() * 100
    if hasattr(returns.index, 'tz') and returns.index.tz is not None:
        returns.index = returns.index.tz_localize(None)
    return returns

def calculate_beta(returns, benchmark_returns):
    """Calculate beta using linear regression"""
    if len(returns) < 2 or len(benchmark_returns) < 2:
        return None, None, None
    
    returns_df = pd.DataFrame({'returns': returns})
    benchmark_df = pd.DataFrame({'benchmark': benchmark_returns})
    
    merged = returns_df.join(benchmark_df, how='inner')
    merged = merged.dropna()
    
    if len(merged) < 10:
        st.warning(f"⚠️ Only {len(merged)} overlapping data points found. Need at least 10 for reliable beta calculation.")
        return None, None, None
    
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

def fetch_live_stock_price(symbol):
    """Fetch current live stock price"""
    try:
        ticker = symbol + '.NS' if not symbol.endswith('.NS') else symbol
        stock = yf.Ticker(ticker)
        
        info = stock.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if current_price is None:
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
        
        stock_df = fetch_stock_data(symbol, start_date, end_date)
        benchmark_df = fetch_index_data(benchmark, start_date, end_date)
        
        if stock_df is None or benchmark_df is None or stock_df.empty or benchmark_df.empty:
            return None
        
        stock_returns = calculate_returns(stock_df['Close'])
        bench_returns = calculate_returns(benchmark_df['Close'])
        
        beta, _, _ = calculate_beta(stock_returns, bench_returns)
        
        return beta
    except:
        return None

def scrape_holdings_from_groww(amfi_code):
    """Scrape real-time holdings from Groww website"""
    try:
        import re
        from bs4 import BeautifulSoup
        
        # Groww URL format
        url = f"https://groww.in/mutual-funds/{amfi_code}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        st.info(f"🔍 Scraping holdings from Groww for AMFI {amfi_code}...")
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            st.warning(f"⚠️ Could not access Groww (Status {response.status_code}). Using fallback data.")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find holdings table
        holdings_container = soup.find('div', {'class': 'holdings101TableContainer'})
        
        if not holdings_container:
            # Try alternative selectors
            holdings_container = soup.find('table', class_=re.compile('.*holding.*', re.I))
        
        if not holdings_container:
            st.warning("⚠️ Could not find holdings table on Groww. Structure may have changed.")
            return None
        
        holdings = []
        
        # Try to parse table rows
        rows = holdings_container.find_all('tr')
        
        for row in rows[1:]:  # Skip header
            cols = row.find_all('td')
            if len(cols) >= 2:
                try:
                    # Extract stock name and allocation
                    stock_name = cols[0].get_text(strip=True)
                    allocation_text = cols[1].get_text(strip=True)
                    
                    # Extract percentage
                    allocation = float(allocation_text.replace('%', '').strip())
                    
                    # Convert company name to ticker symbol (approximate)
                    ticker = convert_company_name_to_ticker(stock_name)
                    
                    if ticker and allocation > 0:
                        holdings.append((ticker, allocation))
                    
                except (ValueError, IndexError) as e:
                    continue
        
        if holdings:
            st.success(f"✅ Successfully scraped {len(holdings)} holdings from Groww!")
            return {
                'name': f'Fund {amfi_code}',
                'holdings': holdings[:10],  # Top 10
                'source': 'Groww (Live)'
            }
        
        return None
        
    except Exception as e:
        st.warning(f"⚠️ Error scraping Groww: {str(e)}")
        return None

def convert_company_name_to_ticker(company_name):
    """Convert company name to NSE ticker symbol"""
    # Common mappings
    name_to_ticker = {
        'HDFC Bank': 'HDFCBANK',
        'HDFC': 'HDFCBANK',
        'ICICI Bank': 'ICICIBANK',
        'State Bank of India': 'SBIN',
        'SBI': 'SBIN',
        'Reliance Industries': 'RELIANCE',
        'Reliance': 'RELIANCE',
        'Infosys': 'INFY',
        'TCS': 'TCS',
        'Tata Consultancy Services': 'TCS',
        'ITC': 'ITC',
        'Bharti Airtel': 'BHARTIARTL',
        'Airtel': 'BHARTIARTL',
        'Kotak Mahindra Bank': 'KOTAKBANK',
        'Kotak Bank': 'KOTAKBANK',
        'Hindustan Unilever': 'HINDUNILVR',
        'HUL': 'HINDUNILVR',
        'Axis Bank': 'AXISBANK',
        'Larsen & Toubro': 'LT',
        'L&T': 'LT',
        'Bajaj Finance': 'BAJFINANCE',
        'Maruti Suzuki': 'MARUTI',
        'Asian Paints': 'ASIANPAINT',
        'Titan Company': 'TITAN',
        'Wipro': 'WIPRO',
        'HCL Technologies': 'HCLTECH',
        'Tech Mahindra': 'TECHM',
        'Sun Pharma': 'SUNPHARMA',
        'Dr. Reddy': 'DRREDDY',
        'Nestle India': 'NESTLEIND',
        'UltraTech Cement': 'ULTRACEMCO',
        'Power Grid': 'POWERGRID',
        'NTPC': 'NTPC',
        'Coal India': 'COALINDIA',
        'Tata Steel': 'TATASTEEL',
        'Tata Motors': 'TATAMOTORS',
        'Mahindra & Mahindra': 'M&M',
        'M&M': 'M&M',
        'Adani Enterprises': 'ADANIENT',
        'Adani Ports': 'ADANIPORTS',
        'JSW Steel': 'JSWSTEEL',
        'Bajaj Auto': 'BAJAJ-AUTO',
        'Hero MotoCorp': 'HEROMOTOCO',
        'Grasim Industries': 'GRASIM',
        'Cipla': 'CIPLA',
        'Divis Laboratories': 'DIVISLAB',
        'Eicher Motors': 'EICHERMOT',
        'SBI Life': 'SBILIFE',
        'HDFC Life': 'HDFCLIFE',
        'ICICI Prudential': 'ICICIPRULI',
        'Bajaj Finserv': 'BAJAJFINSV',
        'IndusInd Bank': 'INDUSINDBK',
        'Tata Consumer': 'TATACONSUM',
        'Britannia': 'BRITANNIA',
        'Dabur': 'DABUR',
        'Godrej Consumer': 'GODREJCP',
        'Pidilite': 'PIDILITIND',
        'Shree Cement': 'SHREECEM',
        'Berger Paints': 'BERGEPAINT'
    }
    
    # Try exact match first
    if company_name in name_to_ticker:
        return name_to_ticker[company_name]
    
    # Try partial match
    company_name_lower = company_name.lower()
    for key, value in name_to_ticker.items():
        if key.lower() in company_name_lower or company_name_lower in key.lower():
            return value
    
    # Try to extract ticker-like pattern
    # If company name has uppercase words, take first word
    words = company_name.strip().split()
    if words:
        potential_ticker = words[0].upper()
        if len(potential_ticker) >= 3:
            return potential_ticker
    
    return None

def scrape_mf_holdings_moneycontrol(amfi_code):
    """Get holdings data - first try Groww, then fallback to static data"""
    
    # First, try scraping from Groww
    groww_data = scrape_holdings_from_groww(amfi_code)
    if groww_data:
        return groww_data
    
    # Fallback to known holdings for popular funds
    st.info("📋 Using factsheet data as fallback...")
    
    known_holdings = {
        '147844': {
            'name': 'SBI Blue Chip Fund',
            'holdings': [
                ('RELIANCE', 8.5),
                ('ICICIBANK', 7.2),
                ('HDFCBANK', 6.8),
                ('INFY', 5.9),
                ('TCS', 5.4),
                ('ITC', 4.8),
                ('BHARTIARTL', 4.2),
                ('KOTAKBANK', 3.9),
                ('HINDUNILVR', 3.5),
                ('AXISBANK', 3.2)
            ],
            'source': 'Factsheet (Static)'
        },
        '119551': {
            'name': 'HDFC Top 100 Fund',
            'holdings': [
                ('HDFCBANK', 8.1),
                ('RELIANCE', 7.5),
                ('ICICIBANK', 6.9),
                ('INFY', 6.2),
                ('TCS', 5.8),
                ('KOTAKBANK', 4.5),
                ('BHARTIARTL', 4.1),
                ('ITC', 3.8),
                ('SBIN', 3.5),
                ('HINDUNILVR', 3.2)
            ],
            'source': 'Factsheet (Static)'
        },
        '120503': {
            'name': 'ICICI Prudential Bluechip Fund',
            'holdings': [
                ('ICICIBANK', 8.2),
                ('HDFCBANK', 7.8),
                ('RELIANCE', 7.1),
                ('INFY', 6.5),
                ('TCS', 5.9),
                ('BHARTIARTL', 4.8),
                ('KOTAKBANK', 4.3),
                ('ITC', 3.9),
                ('HINDUNILVR', 3.6),
                ('SBIN', 3.3)
            ],
            'source': 'Factsheet (Static)'
        }
    }
    
    return known_holdings.get(amfi_code, None)

def calculate_dynamic_nav(holdings_data, total_units=10000000):
    """Calculate NAV dynamically based on current holdings prices"""
    total_value = 0
    
    for holding in holdings_data:
        if holding['current_price'] and holding['quantity']:
            total_value += holding['current_price'] * holding['quantity']
    
    nav = total_value / total_units if total_units > 0 else 0
    
    return nav, total_value

def fetch_mf_nav(amfi_code, start_date, end_date):
    """Fetch mutual fund NAV data from AMFI website"""
    try:
        url = "https://www.amfiindia.com/spages/NAVAll.txt"
        
        st.info(f"🔍 Fetching NAV data for AMFI code: {amfi_code}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            st.error(f"Failed to fetch AMFI data. Status code: {response.status_code}")
            return None, None
        
        lines = response.text.strip().split('\n')
        
        scheme_found = False
        scheme_name = None
        nav_value = None
        nav_date = None
        
        for line in lines:
            if not line.strip() or line.startswith('Scheme Code'):
                continue
            
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
        
        hist_url = f"https://api.mfapi.in/mf/{amfi_code}"
        
        try:
            hist_response = requests.get(hist_url, timeout=10)
            if hist_response.status_code == 200:
                hist_data = hist_response.json()
                
                if 'data' in hist_data:
                    nav_df = pd.DataFrame(hist_data['data'])
                    nav_df['date'] = pd.to_datetime(nav_df['date'], format='%d-%m-%Y')
                    nav_df['nav'] = pd.to_numeric(nav_df['nav'], errors='coerce')
                    nav_df = nav_df.sort_values('date')
                    
                    if hasattr(nav_df['date'], 'dt'):
                        nav_df['date'] = pd.to_datetime(nav_df['date']).dt.tz_localize(None)
                    
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
        
        if nav_value and nav_date:
            st.warning("⚠️ Only current NAV available. Historical data limited.")
            try:
                nav_float = float(nav_value)
                date_obj = pd.to_datetime(nav_date, format='%d-%b-%Y')
                
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
    
    fig.add_trace(go.Scatter(
        x=benchmark_returns,
        y=returns,
        mode='markers',
        name='Returns',
        marker=dict(size=8, color='#4F46E5', opacity=0.6)
    ))
    
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

# ==================== TABS ====================

tab1, tab2, tab3 = st.tabs(["📊 Portfolio Beta", "💼 Mutual Fund Beta", "ℹ️ About"])

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
    
    if st.button("🔍 Calculate Portfolio Beta", type="primary", use_container_width=True):
        if not stocks_data:
            st.error("❌ Please add at least one stock with allocation!")
        elif sum([s["Allocation"] for s in stocks_data]) > 100:
            st.error("❌ Total allocation cannot exceed 100%!")
        else:
            with st.spinner("📊 Fetching real market data and calculating metrics..."):
                try:
                    benchmark_df = fetch_index_data(benchmark, start_date, end_date)
                    
                    if benchmark_df is None or benchmark_df.empty:
                        st.error("❌ Could not fetch benchmark data. Please check your internet connection.")
                    else:
                        benchmark_returns = calculate_returns(benchmark_df['Close'])
                        
                        stock_betas = []
                        all_stock_returns = []
                        valid_stocks = []
                        
                        progress_bar = st.progress(0)
                        for idx, stock in enumerate(stocks_data):
                            stock_df = fetch_stock_data(stock['Symbol'], start_date, end_date)
                            
                            if stock_df is not None and not stock_df.empty:
                                stock_returns = calculate_returns(stock_df['Close'])
                                
                                stock_beta, _, _ = calculate_beta(stock_returns, benchmark_returns)
                                
                                if stock_beta is not None:
                                    contribution = stock_beta * (stock['Allocation'] / 100)
                                    stock_betas.append({
                                        'Symbol': stock['Symbol'],
                                        'Allocation': stock['Allocation'],
                                        'Beta': stock_beta,
                                        'Contribution': contribution
                                    })
                                    
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
                            portfolio_returns_df = pd.concat(all_stock_returns, axis=1)
                            portfolio_returns = portfolio_returns_df.sum(axis=1)
                            
                            beta, r_squared, correlation = calculate_beta(
                                portfolio_returns, 
                                benchmark_returns
                            )
                            
                            if beta is None:
                                st.error("❌ Could not calculate beta. Insufficient data overlap.")
                            else:
                                mean_return = portfolio_returns.mean() * 252
                                mean_bench = benchmark_returns.mean() * 252
                                alpha = mean_return - (beta * mean_bench)
                                volatility = portfolio_returns.std() * np.sqrt(252)
                                sharpe_ratio = (mean_return - 5) / volatility if volatility > 0 else 0
                                
                                st.divider()
                                st.success("✅ Analysis Complete!")
                                
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
                                
                                if beta < 0.8:
                                    st.success("🟢 **Low Risk - Defensive Portfolio**\n\nYour portfolio is less volatile than the market.")
                                elif beta < 1.2:
                                    st.info("🔵 **Moderate Risk - Market-aligned**\n\nYour portfolio moves in line with the benchmark.")
                                else:
                                    st.warning("🔴 **High Risk - Aggressive Portfolio**\n\nYour portfolio is more volatile than the market.")
                                
                                plot_df = pd.DataFrame({
                                    'Portfolio': portfolio_returns,
                                    'Benchmark': benchmark_returns
                                }).dropna()
                                
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
                    nav_df, scheme_info = fetch_mf_nav(mf_scheme.strip(), mf_start_date, mf_end_date)
                    
                    if nav_df is None or nav_df.empty:
                        st.error("❌ Could not fetch mutual fund data. Please verify the AMFI code.")
                        st.info("💡 Common AMFI Codes:\n- 147844: SBI Blue Chip Fund\n- 119551: HDFC Top 100 Fund\n- 120503: ICICI Prudential Bluechip Fund")
                    else:
                        st.success(f"✅ Found scheme: **{scheme_info['scheme_name']}**")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Fund House", scheme_info['fund_house'])
                        with col2:
                            st.metric("Scheme Type", scheme_info['scheme_type'])
                        with col3:
                            st.metric("Category", scheme_info['scheme_category'])
                        
                        st.divider()
                        
                        benchmark_df = fetch_index_data(mf_benchmark, mf_start_date, mf_end_date)
                        
                        if benchmark_df is None or benchmark_df.empty:
                            st.error("❌ Could not fetch benchmark data.")
                        else:
                            nav_returns = calculate_returns(nav_df['nav'])
                            benchmark_returns = calculate_returns(benchmark_df['Close'])
                            
                            st.info(f"""
                            📊 **Data Info:**
                            - NAV data points: {len(nav_df)}
                            - NAV date range: {nav_df.index.min().strftime('%Y-%m-%d')} to {nav_df.index.max().strftime('%Y-%m-%d')}
                            - Benchmark data points: {len(benchmark_df)}
                            - Benchmark date range: {benchmark_df.index.min().strftime('%Y-%m-%d')} to {benchmark_df.index.max().strftime('%Y-%m-%d')}
                            """)
                            
                            nav_monthly = nav_df['nav'].resample('M').last()
                            benchmark_monthly = benchmark_df['Close'].resample('M').last()
                            
                            nav_returns_monthly = calculate_returns(nav_monthly)
                            benchmark_returns_monthly = calculate_returns(benchmark_monthly)
                            
                            st.info(f"""
                            📊 **Monthly Resampled Data:**
                            - NAV monthly points: {len(nav_returns_monthly)}
                            - Benchmark monthly points: {len(benchmark_returns_monthly)}
                            """)
                            
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
                                mean_return = nav_returns_monthly.mean() * 12
                                mean_bench = benchmark_returns_monthly.mean() * 12
                                alpha = mean_return - (beta * mean_bench)
                                volatility = nav_returns_monthly.std() * np.sqrt(12)
                                sharpe_ratio = (mean_return - 5) / volatility if volatility > 0 else 0
                                
                                plot_df = pd.DataFrame({
                                    'NAV_Return': nav_returns_monthly,
                                    'Benchmark_Return': benchmark_returns_monthly
                                }).dropna()
                                
                                st.success(f"✅ Successfully calculated beta using {len(plot_df)} monthly data points")
                                
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
                                
                                if beta < 0.8:
                                    st.success("🟢 **Low Risk Fund**\n\nThis fund is less volatile than the benchmark, suitable for conservative investors.")
                                elif beta < 1.2:
                                    st.info("🔵 **Moderate Risk Fund**\n\nThis fund moves in line with the benchmark.")
                                else:
                                    st.warning("🔴 **High Risk Fund**\n\nThis fund is more volatile than the benchmark, suitable for aggressive investors.")
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
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
                                    fig_reg = plot_beta_regression(
                                        plot_df['NAV_Return'].values,
                                        plot_df['Benchmark_Return'].values
                                    )
                                    st.plotly_chart(fig_reg, use_container_width=True)
                                
                                nav_cumulative = (1 + nav_returns).cumprod() - 1
                                bench_cumulative = (1 + benchmark_returns).cumprod() - 1
                                
                                common_dates = nav_cumulative.index.intersection(bench_cumulative.index)
                                if len(common_dates) > 0:
                                    fig_returns = go.Figure()
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
                                
                                st.subheader("📈 Data Summary")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Data Points", len(nav_df))
                                with col2:
                                    st.metric("Latest NAV", f"₹{nav_df['nav'].iloc[-1]:.2f}")
                                with col3:
                                    st.metric("Volatility (Annual)", f"{volatility*100:.2f}%")
                                
                                # HOLDINGS SECTION
                                st.divider()
                                st.subheader("📋 Portfolio Holdings Analysis")
                                
                                st.warning("""
                                ⚠️ **Important Note About Holdings Data:**
                                
                                Holdings data shown below is based on:
                                - **Latest available factsheets** (manually updated)
                                - **Not real-time** - actual allocations may have changed
                                - For most accurate data, check the fund's latest factsheet at the AMC website
                                
                                To get real-time holdings, you would need to:
                                1. Scrape from Moneycontrol/ValueResearch (requires web scraping)
                                2. Use paid APIs like MorningStar
                                3. Parse PDF factsheets automatically
                                """)
                                
                                holdings_info = scrape_mf_holdings_moneycontrol(mf_scheme.strip())
                                
                                # CSV Upload Option
                                st.divider()
                                with st.expander("📤 Or Upload Custom Holdings CSV", expanded=False):
                                    st.markdown("""
                                    **Upload a CSV file with holdings data:**
                                    - Column A: Stock Tickers (without .NS, e.g., RELIANCE, TCS, INFY)
                                    - Column B: Weight/Allocation in % (e.g., 8.5, 7.2, 6.8)
                                    
                                    **CSV Format Example:**
                                    ```
                                    Ticker,Weight
                                    RELIANCE,8.5
                                    TCS,7.2
                                    HDFCBANK,6.8
                                    INFY,5.9
                                    ```
                                    """)
                                    
                                    uploaded_file = st.file_uploader(
                                        "Choose CSV file", 
                                        type=['csv'],
                                        key="holdings_csv"
                                    )
                                    
                                    if uploaded_file is not None:
                                        try:
                                            # Read CSV
                                            holdings_csv = pd.read_csv(uploaded_file)
                                            
                                            # Display preview
                                            st.success("✅ CSV file uploaded successfully!")
                                            st.caption("Preview of uploaded data:")
                                            st.dataframe(holdings_csv.head(10), use_container_width=True)
                                            
                                            # Validate columns
                                            if len(holdings_csv.columns) < 2:
                                                st.error("❌ CSV must have at least 2 columns (Ticker and Weight)")
                                            else:
                                                # Get column names (flexible - works with any column names)
                                                ticker_col = holdings_csv.columns[0]
                                                weight_col = holdings_csv.columns[1]
                                                
                                                st.info(f"📊 Detected: Ticker column = '{ticker_col}', Weight column = '{weight_col}'")
                                                
                                                # Clean and validate data
                                                holdings_csv[ticker_col] = holdings_csv[ticker_col].astype(str).str.strip().str.upper()
                                                holdings_csv[weight_col] = pd.to_numeric(holdings_csv[weight_col], errors='coerce')
                                                
                                                # Remove NaN values
                                                holdings_csv = holdings_csv.dropna()
                                                
                                                if holdings_csv.empty:
                                                    st.error("❌ No valid data found in CSV")
                                                else:
                                                    # Create holdings info from CSV
                                                    csv_holdings = []
                                                    for _, row in holdings_csv.iterrows():
                                                        ticker = row[ticker_col]
                                                        weight = float(row[weight_col])
                                                        if ticker and weight > 0:
                                                            csv_holdings.append((ticker, weight))
                                                    
                                                    if csv_holdings:
                                                        holdings_info = {
                                                            'name': f'Custom Portfolio from CSV',
                                                            'holdings': csv_holdings,
                                                            'source': 'Uploaded CSV'
                                                        }
                                                        st.success(f"✅ Loaded {len(csv_holdings)} holdings from CSV")
                                                        st.info("💡 Scroll down to see the analysis with your uploaded holdings")
                                                    else:
                                                        st.error("❌ No valid holdings found in CSV")
                                        
                                        except Exception as e:
                                            st.error(f"❌ Error reading CSV: {str(e)}")
                                            st.info("Please ensure your CSV has two columns: Ticker and Weight")
                                
                                if holdings_info:
                                    st.success(f"✅ Found holdings data for: **{holdings_info['name']}**")
                                    
                                    # Show data source
                                    if holdings_info.get('source') == 'Groww (Live)':
                                        st.success("🌐 **Data Source:** Scraped live from Groww")
                                    elif holdings_info.get('source') == 'Uploaded CSV':
                                        st.success("📤 **Data Source:** Your uploaded CSV file")
                                    else:
                                        st.info(f"📋 **Data Source:** {holdings_info.get('source', 'Factsheet')}")
                                    
                                    holdings_data = []
                                    
                                    progress_bar = st.progress(0)
                                    progress_text = st.empty()
                                    
                                    for idx, (symbol, allocation_pct) in enumerate(holdings_info['holdings']):
                                        progress_text.text(f"Fetching live data for {symbol}...")
                                        
                                        current_price = fetch_live_stock_price(symbol)
                                        stock_beta = calculate_stock_beta_live(symbol, mf_benchmark, period_days=365)
                                        
                                        if current_price:
                                            # Calculate based on given allocation
                                            portfolio_value = 1000000000  # Assume 100 Cr fund
                                            allocation_value = (allocation_pct / 100) * portfolio_value
                                            quantity = allocation_value / current_price
                                            
                                            holdings_data.append({
                                                'Symbol': symbol,
                                                'Current Price': current_price,
                                                'Beta': stock_beta if stock_beta else 0,
                                                'Allocation %': allocation_pct,
                                                'Quantity': quantity,
                                                'Market Value': current_price * quantity
                                            })
                                        
                                        progress_bar.progress((idx + 1) / len(holdings_info['holdings']))
                                    
                                    progress_bar.empty()
                                    progress_text.empty()
                                    
                                    if holdings_data:
                                        # Calculate dynamic NAV
                                        dynamic_nav, total_portfolio_value = calculate_dynamic_nav(
                                            [{'current_price': h['Current Price'], 'quantity': h['Quantity']} for h in holdings_data]
                                        )
                                        
                                        st.success(f"🔴 **LIVE NAV (Top Holdings Only):** ₹{dynamic_nav:.4f}")
                                        st.caption("⚡ Calculated from top 10 holdings only. Actual NAV includes all holdings + cash + other assets")
                                        
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Top 10 Holdings Value", f"₹{total_portfolio_value/10000000:.2f} Cr")
                                        with col2:
                                            weighted_beta = sum([h['Beta'] * h['Allocation %'] / 100 for h in holdings_data])
                                            st.metric("Holdings Beta (Weighted)", f"{weighted_beta:.3f}")
                                        with col3:
                                            total_alloc = sum([h['Allocation %'] for h in holdings_data])
                                            st.metric("Holdings Coverage", f"{total_alloc:.1f}%")
                                        
                                        st.subheader("📊 Live Holdings Breakdown")
                                        st.caption("🔴 Prices updated in real-time from market")
                                        
                                        holdings_df = pd.DataFrame(holdings_data)
                                        holdings_df['Current Price'] = holdings_df['Current Price'].round(2)
                                        holdings_df['Beta'] = holdings_df['Beta'].round(3)
                                        holdings_df['Allocation %'] = holdings_df['Allocation %'].round(2)
                                        holdings_df['Quantity'] = holdings_df['Quantity'].round(0)
                                        holdings_df['Market Value'] = holdings_df['Market Value'].round(2)
                                        
                                        def format_value(val):
                                            if val >= 10000000:
                                                return f"₹{val/10000000:.2f} Cr"
                                            elif val >= 100000:
                                                return f"₹{val/100000:.2f} L"
                                            else:
                                                return f"₹{val:.2f}"
                                        
                                        holdings_df['Market Value (Formatted)'] = holdings_df['Market Value'].apply(format_value)
                                        
                                        display_df = holdings_df[['Symbol', 'Current Price', 'Beta', 'Allocation %', 'Quantity', 'Market Value (Formatted)']]
                                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                                        
                                        st.subheader("📊 Holdings Analysis")
                                        
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
                                        
                                        fig_allocation = px.pie(
                                            holdings_df,
                                            values='Allocation %',
                                            names='Symbol',
                                            title='Portfolio Allocation (Top Holdings)'
                                        )
                                        st.plotly_chart(fig_allocation, use_container_width=True)
                                        
                                        st.info("🔄 **Refresh the page** to update stock prices. Holdings allocation data is from latest factsheet.")
                                else:
                                    st.warning(f"""
                                    ⚠️ **Holdings data not available for AMFI code {mf_scheme}**
                                    
                                    Currently available for:
                                    - 147844: SBI Blue Chip Fund
                                    - 119551: HDFC Top 100 Fund  
                                    - 120503: ICICI Prudential Bluechip Fund
                                    
                                    **To add holdings for this fund:**
                                    1. Download the latest factsheet from the AMC website
                                    2. Extract top 10 holdings with allocation %
                                    3. Update the code with this data
                                    
                                    Or implement automatic factsheet parsing (PDF scraping)
                                    """)
                
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

# ===== ABOUT TAB =====
with tab3:
    st.subheader("About This Tool")
    
    st.markdown("""
    ## 📈 Beta Calculator - Real Market Data
    
    ### ✅ Features:
    - Real stock prices from Yahoo Finance
    - Live NAV data from AMFI India
    - Web scraping from Groww for holdings
    - CSV upload for custom portfolios
    - Individual stock beta calculation
    - Dynamic NAV calculation
    - Custom date ranges
    
    ### 📤 CSV Upload Format:
    
    Create a CSV file with 2 columns:
    
    **Column A (Ticker):** Stock symbols without .NS extension
    **Column B (Weight):** Allocation percentage
    
    Example CSV:
    ```
    Ticker,Weight
    RELIANCE,8.5
    TCS,7.2
    HDFCBANK,6.8
    INFY,5.9
    ICICIBANK,5.4
    HINDUNILVR,4.8
    ITC,4.2
    BHARTIARTL,3.9
    KOTAKBANK,3.5
    SBIN,3.2
    ```
    
    **Notes:**
    - Tickers should be NSE symbols (without .NS)
    - Weight should be in percentage (total can be less than 100%)
    - CSV can have any column names - first column = ticker, second = weight
    - Headers are optional
    
    ### 📝 Popular AMFI Codes:
    - 147844 - SBI Blue Chip Fund
    - 119551 - HDFC Top 100 Fund
    - 120503 - ICICI Prudential Bluechip Fund
    
    ### 🌐 Data Sources:
    1. **Groww** - Live web scraping (automatic)
    2. **CSV Upload** - Your custom data
    3. **Factsheet** - Fallback static data
    
    ### ⚠️ Disclaimer:
    For educational purposes only. Not financial advice.
    """)

st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Beta Calculator with Real Market Data</strong></p>
    <p style='font-size: 0.8em;'>💡 Tip: Upload a CSV file for instant analysis of any portfolio!</p>
</div>
""", unsafe_allow_html=True)
