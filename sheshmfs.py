import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from scipy import stats

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
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'portfolio_stocks' not in st.session_state:
    st.session_state.portfolio_stocks = []
if 'results' not in st.session_state:
    st.session_state.results = None

# Title and header
st.title("📈 Portfolio & Mutual Fund Beta Calculator Pro")
st.markdown("**Comprehensive Risk Analysis with Custom Date Ranges**")
st.divider()

# Tabs
tab1, tab2 = st.tabs(["📊 Portfolio Beta", "💼 Mutual Fund Beta"])

def calculate_beta(returns, benchmark_returns):
    """Calculate beta using linear regression"""
    if len(returns) < 2 or len(benchmark_returns) < 2:
        return None, None, None
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(benchmark_returns, returns)
    
    beta = slope
    r_squared = r_value ** 2
    correlation = r_value
    
    return beta, r_squared, correlation

def generate_synthetic_data(start_date, end_date, volatility=10):
    """Generate synthetic return data for demonstration"""
    dates = pd.date_range(start=start_date, end=end_date, freq='M')
    n = len(dates)
    
    # Generate correlated returns
    benchmark_returns = np.random.normal(0, 8, n)
    portfolio_returns = benchmark_returns * 1.2 + np.random.normal(0, volatility, n)
    
    df = pd.DataFrame({
        'Date': dates,
        'Portfolio_Return': portfolio_returns,
        'Benchmark_Return': benchmark_returns
    })
    
    return df

def plot_returns_comparison(df, title="Returns Comparison"):
    """Plot portfolio vs benchmark returns"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Portfolio_Return'],
        mode='lines+markers',
        name='Portfolio',
        line=dict(color='#4F46E5', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Benchmark_Return'],
        mode='lines+markers',
        name='Benchmark',
        line=dict(color='#10B981', width=2)
    ))
    
    fig.update_layout(
        title=title,
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
        name='Monthly Returns',
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
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Portfolio Configuration")
        
        # Benchmark selection
        benchmark = st.selectbox(
            "Benchmark Index",
            ["NIFTY 50", "SENSEX", "NIFTY 500", "NIFTY Midcap 100"],
            key="portfolio_benchmark"
        )
        
        # Time period selection
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
            custom_dates = True
        else:
            # Calculate dates based on selection
            months_map = {
                "6 Months": 6,
                "1 Year": 12,
                "3 Years": 36,
                "5 Years": 60
            }
            months = months_map.get(time_period, 12)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months*30)
            custom_dates = False
        
    with col2:
        st.subheader("Quick Info")
        st.info(f"""
        **Selected Period:**  
        {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}
        
        **Duration:**  
        ~{(end_date - start_date).days // 30} months
        """)
    
    st.divider()
    
    # Portfolio stocks input
    st.subheader("Portfolio Holdings")
    
    num_stocks = st.number_input("Number of stocks", min_value=1, max_value=20, value=3)
    
    stocks_data = []
    for i in range(num_stocks):
        col1, col2 = st.columns([3, 1])
        with col1:
            symbol = st.text_input(f"Stock {i+1} Symbol", key=f"stock_{i}", placeholder="e.g., RELIANCE, TCS")
        with col2:
            allocation = st.number_input(f"Allocation %", min_value=0.0, max_value=100.0, value=0.0, key=f"alloc_{i}")
        
        if symbol and allocation > 0:
            stocks_data.append({"Symbol": symbol, "Allocation": allocation})
    
    # Calculate button
    if st.button("🔍 Calculate Portfolio Beta", type="primary", use_container_width=True):
        if not stocks_data:
            st.error("Please add at least one stock with allocation!")
        elif sum([s["Allocation"] for s in stocks_data]) > 100:
            st.error("Total allocation cannot exceed 100%!")
        else:
            with st.spinner("Calculating portfolio metrics..."):
                # Generate synthetic data
                df = generate_synthetic_data(start_date, end_date)
                
                portfolio_returns = df['Portfolio_Return'].values
                benchmark_returns = df['Benchmark_Return'].values
                
                # Calculate beta
                beta, r_squared, correlation = calculate_beta(portfolio_returns, benchmark_returns)
                
                # Calculate additional metrics
                mean_return = np.mean(portfolio_returns) * 12  # Annualized
                mean_bench = np.mean(benchmark_returns) * 12
                alpha = mean_return - (beta * mean_bench)
                volatility = np.std(portfolio_returns) * np.sqrt(12)
                sharpe_ratio = (mean_return - 5) / volatility  # Assuming 5% risk-free rate
                
                # Generate individual stock betas
                stock_betas = []
                for stock in stocks_data:
                    stock_returns = np.random.normal(0, 12, len(benchmark_returns))
                    stock_beta, _, _ = calculate_beta(stock_returns, benchmark_returns)
                    contribution = stock_beta * (stock['Allocation'] / 100)
                    stock_betas.append({
                        'Symbol': stock['Symbol'],
                        'Allocation': stock['Allocation'],
                        'Beta': stock_beta,
                        'Contribution': contribution
                    })
                
                # Store results
                st.session_state.results = {
                    'beta': beta,
                    'alpha': alpha,
                    'r_squared': r_squared,
                    'correlation': correlation,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'df': df,
                    'stock_betas': stock_betas,
                    'benchmark': benchmark,
                    'start_date': start_date,
                    'end_date': end_date,
                    'custom': custom_dates
                }
    
    # Display results
    if st.session_state.results and 'beta' in st.session_state.results:
        st.divider()
        st.subheader("📊 Analysis Results")
        
        results = st.session_state.results
        
        # Date range info
        st.info(f"""
        📅 **Analysis Period:** {results['start_date'].strftime('%b %d, %Y')} → {results['end_date'].strftime('%b %d, %Y')}  
        {'🔧 Custom Date Range' if results['custom'] else '📆 Standard Period'}
        """)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Portfolio Beta", f"{results['beta']:.3f}", help="Volatility vs benchmark")
        with col2:
            st.metric("Alpha (%)", f"{results['alpha']:.2f}", 
                     delta="Positive" if results['alpha'] > 0 else "Negative")
        with col3:
            st.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}", help="Risk-adjusted return")
        with col4:
            st.metric("R² (%)", f"{results['r_squared']*100:.2f}", help="Correlation strength")
        
        # Risk assessment
        beta_val = results['beta']
        if beta_val < 0.8:
            risk_color = "🟢"
            risk_text = "Low Risk - Defensive Portfolio"
            risk_desc = "Your portfolio is less volatile than the market, suitable for conservative investors."
        elif beta_val < 1.2:
            risk_color = "🔵"
            risk_text = "Moderate Risk - Market-aligned"
            risk_desc = "Your portfolio moves in line with the market benchmark."
        else:
            risk_color = "🔴"
            risk_text = "High Risk - Aggressive Portfolio"
            risk_desc = "Your portfolio is more volatile than the market, suitable for aggressive investors."
        
        st.success(f"""
        {risk_color} **Risk Assessment: {risk_text}**  
        {risk_desc}
        """)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = plot_returns_comparison(results['df'])
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = plot_beta_regression(
                results['df']['Portfolio_Return'].values,
                results['df']['Benchmark_Return'].values
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Stock betas table
        if results['stock_betas']:
            st.subheader("Individual Stock Analysis")
            stock_df = pd.DataFrame(results['stock_betas'])
            stock_df['Beta'] = stock_df['Beta'].round(3)
            stock_df['Contribution'] = stock_df['Contribution'].round(3)
            stock_df['Allocation'] = stock_df['Allocation'].round(2)
            
            st.dataframe(stock_df, use_container_width=True, hide_index=True)

# ===== MUTUAL FUND BETA TAB =====
with tab2:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Mutual Fund Configuration")
        
        # MF scheme input
        mf_scheme = st.text_input(
            "Enter Mutual Fund Details",
            placeholder="AMFI Code / Scheme Name / ISIN (e.g., 118989)",
            help="Enter AMFI code, scheme name, or ISIN to fetch fund details"
        )
        
        st.info("💡 The app will fetch holdings and NAV data to calculate beta")
        
        # Benchmark and time period
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            mf_benchmark = st.selectbox(
                "Benchmark Index",
                ["NIFTY 50", "SENSEX", "NIFTY 500"],
                key="mf_benchmark"
            )
        
        with col_b2:
            mf_time_options = ["1 Year", "3 Years", "5 Years", "Custom Date Range"]
            mf_time_period = st.selectbox("Analysis Period", mf_time_options, key="mf_time")
        
        # Custom date range for MF
        if mf_time_period == "Custom Date Range":
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
            months = months_map.get(mf_time_period, 12)
            mf_end_date = datetime.now()
            mf_start_date = mf_end_date - timedelta(days=months*30)
            mf_custom = False
    
    with col2:
        st.subheader("Period Info")
        st.info(f"""
        **Analysis Period:**  
        {mf_start_date.strftime('%b %d, %Y')} to {mf_end_date.strftime('%b %d, %Y')}
        
        **Duration:**  
        ~{(mf_end_date - mf_start_date).days // 30} months
        """)
    
    # Calculate MF beta
    if st.button("📈 Analyze Mutual Fund", type="primary", use_container_width=True):
        if not mf_scheme:
            st.error("Please enter mutual fund details!")
        else:
            with st.spinner("Analyzing mutual fund scheme..."):
                # Generate synthetic NAV data
                df = generate_synthetic_data(mf_start_date, mf_end_date, volatility=8)
                df['NAV'] = 50 + df['Portfolio_Return'].cumsum() * 0.5
                df['Benchmark_Index'] = 1000 + df['Benchmark_Return'].cumsum() * 10
                
                # Calculate returns from NAV
                nav_returns = df['NAV'].pct_change().dropna() * 100
                bench_returns = df['Benchmark_Index'].pct_change().dropna() * 100
                
                # Calculate beta
                beta, r_squared, correlation = calculate_beta(nav_returns.values, bench_returns.values)
                
                # Synthetic holdings data
                holdings = [
                    {"Stock": "RELIANCE", "Sector": "Energy", "Allocation": 8.5, "Beta": 1.12},
                    {"Stock": "TCS", "Sector": "IT", "Allocation": 7.2, "Beta": 0.85},
                    {"Stock": "HDFCBANK", "Sector": "Banking", "Allocation": 6.8, "Beta": 1.05},
                    {"Stock": "INFY", "Sector": "IT", "Allocation": 5.9, "Beta": 0.82},
                    {"Stock": "ICICIBANK", "Sector": "Banking", "Allocation": 5.4, "Beta": 1.15},
                ]
                
                weighted_beta = sum([h["Allocation"] * h["Beta"] / 100 for h in holdings])
                
                # Display results
                st.divider()
                st.subheader("📊 Mutual Fund Analysis")
                
                # Date info
                st.info(f"""
                📅 **Analysis Period:** {mf_start_date.strftime('%b %d, %Y')} → {mf_end_date.strftime('%b %d, %Y')}  
                {'🔧 Custom Date Range' if mf_custom else '📆 Standard Period'}
                """)
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("NAV-based Beta", f"{beta:.3f}")
                with col2:
                    st.metric("Weighted Holdings Beta", f"{weighted_beta:.3f}")
                with col3:
                    st.metric("R² (%)", f"{r_squared*100:.2f}")
                
                # Risk assessment
                if beta < 0.8:
                    st.success("🟢 **Low Risk Fund** - Less volatile than benchmark")
                elif beta < 1.2:
                    st.info("🔵 **Moderate Risk Fund** - Moves with benchmark")
                else:
                    st.warning("🔴 **High Risk Fund** - More volatile than benchmark")
                
                # Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_nav = go.Figure()
                    fig_nav.add_trace(go.Scatter(x=df['Date'], y=df['NAV'], name='NAV', line=dict(color='#4F46E5')))
                    fig_nav.update_layout(title="NAV Trend", xaxis_title="Date", yaxis_title="NAV", height=400)
                    st.plotly_chart(fig_nav, use_container_width=True)
                
                with col2:
                    fig_reg = plot_beta_regression(nav_returns.values, bench_returns.values)
                    st.plotly_chart(fig_reg, use_container_width=True)
                
                # Holdings table
                st.subheader("Top Holdings Analysis")
                holdings_df = pd.DataFrame(holdings)
                st.dataframe(holdings_df, use_container_width=True, hide_index=True)
                
                # Sector allocation
                sector_alloc = holdings_df.groupby('Sector')['Allocation'].sum().reset_index()
                fig_sector = px.pie(sector_alloc, values='Allocation', names='Sector', 
                                   title='Sector Allocation')
                st.plotly_chart(fig_sector, use_container_width=True)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Beta Calculator Pro v1.0</strong> | Comprehensive Portfolio & Mutual Fund Analysis</p>
    <p style='font-size: 0.8em;'>Note: This is a demonstration app with simulated data. 
    For production use, integrate real-time APIs for stock prices, NAV, and holdings data.</p>
</div>
""", unsafe_allow_html=True)
