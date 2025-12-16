import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import time

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Indian Stock Scout - LIVE Scanner", page_icon="🎯", layout="wide")

# Custom CSS
st.markdown("""<style>
.main-header{font-size:2.5rem;font-weight:700;color:#1f77b4;text-align:center;margin-bottom:1rem}
.sub-header{font-size:1.5rem;font-weight:600;color:#333;margin:1rem 0}
.qualified{background:#d4edda;border-left:5px solid #28a745;padding:1rem;border-radius:8px;margin:0.5rem 0}
.watchlist{background:#fff3cd;border-left:5px solid #ffc107;padding:1rem;border-radius:8px;margin:0.5rem 0}
.not-qualified{background:#f8d7da;border-left:5px solid #dc3545;padding:1rem;border-radius:8px;margin:0.5rem 0}
.metric-card{background:#f8f9fb;padding:0.8rem;border-radius:8px;border-left:4px solid #1f77b4;margin:0.5rem 0}
</style>""", unsafe_allow_html=True)

# Stock universe
NSE_STOCKS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC', 'SBIN', 
    'BHARTIARTL', 'KOTAKBANK', 'LT', 'AXISBANK', 'ASIANPAINT', 'MARUTI', 'HCLTECH',
    'BAJFINANCE', 'WIPRO', 'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'ONGC',
    'TATAMOTORS', 'NTPC', 'POWERGRID', 'JSWSTEEL', 'M&M', 'TECHM', 'ADANIENT', 'ADANIPORTS',
    'COALINDIA', 'HINDALCO', 'TATASTEEL', 'BAJAJFINSV', 'DIVISLAB', 'DRREDDY', 'GRASIM',
    'CIPLA', 'BRITANNIA', 'EICHERMOT', 'HEROMOTOCO', 'APOLLOHOSP', 'INDUSINDBK', 'UPL',
    'BPCL', 'SBILIFE', 'HDFCLIFE', 'BAJAJ-AUTO', 'VEDL', 'TATACONSUM', 'GODREJCP',
    'DABUR', 'PIDILITIND', 'HAVELLS', 'BERGEPAINT', 'SIEMENS', 'AMBUJACEM', 'DLF',
    'INDIGO', 'BANDHANBNK', 'CHOLAFIN', 'GAIL', 'MUTHOOTFIN', 'MARICO', 'NMDC',
    'TATAPOWER', 'LUPIN', 'PNB', 'BANKBARODA', 'CANBK', 'IRCTC', 'BEL', 'HAL',
    'DIXON', 'TRENT', 'DMART', 'NAUKRI', 'ZOMATO', 'MOTHERSON', 'ESCORTS', 'TVSMOTOR',
    'IGL', 'MGL', 'LICI', 'VOLTAS', 'PERSISTENT', 'COFORGE', 'LTIM', 'MPHASIS'
]

SECTOR_MAP = {
    'RELIANCE': 'Energy', 'TCS': 'IT', 'HDFCBANK': 'Banking', 'INFY': 'IT', 'ICICIBANK': 'Banking',
    'HINDUNILVR': 'FMCG', 'ITC': 'FMCG', 'SBIN': 'Banking', 'BHARTIARTL': 'Telecom', 'KOTAKBANK': 'Banking',
    'LT': 'Infrastructure', 'AXISBANK': 'Banking', 'ASIANPAINT': 'Paints', 'MARUTI': 'Auto', 'HCLTECH': 'IT',
    'BAJFINANCE': 'NBFC', 'WIPRO': 'IT', 'SUNPHARMA': 'Pharma', 'TITAN': 'Consumer', 'ULTRACEMCO': 'Cement',
    'NESTLEIND': 'FMCG', 'ONGC': 'Energy', 'TATAMOTORS': 'Auto', 'NTPC': 'Power', 'POWERGRID': 'Power',
    'JSWSTEEL': 'Metals', 'M&M': 'Auto', 'TECHM': 'IT', 'ADANIENT': 'Conglomerate', 'ADANIPORTS': 'Infrastructure',
    'COALINDIA': 'Mining', 'HINDALCO': 'Metals', 'TATASTEEL': 'Metals', 'BAJAJFINSV': 'NBFC', 'DIVISLAB': 'Pharma'
}

@st.cache_data(ttl=300)
def fetch_stock_data(symbol):
    """Fetch real-time data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period="3mo", interval="1d")
        
        if hist.empty:
            return None
        
        # Calculate indicators
        closes = hist['Close'].values
        highs = hist['High'].values
        lows = hist['Low'].values
        volumes = hist['Volume'].values
        
        price = closes[-1]
        prev_close = closes[-2] if len(closes) > 1 else price
        change = ((price - prev_close) / prev_close) * 100
        
        # RSI
        rsi = calculate_rsi(closes)
        
        # MACD
        macd = calculate_macd(closes)
        
        # Bollinger Bands
        bb_position = calculate_bb_position(closes)
        
        # Volume
        vol_multiple = calculate_volume_multiple(volumes)
        
        # Trend
        trend = detect_trend(closes)
        
        return {
            'symbol': symbol,
            'price': price,
            'change': change,
            'rsi': rsi,
            'macd': macd,
            'bb_position': bb_position,
            'vol_multiple': vol_multiple,
            'trend': trend,
            'closes': closes,
            'highs': highs,
            'lows': lows,
            'volumes': volumes
        }
    except Exception as e:
        return None

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    if len(prices) < period + 1:
        return 50
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices):
    """Calculate MACD"""
    if len(prices) < 26:
        return 0
    
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    return ema12 - ema26

def calculate_ema(prices, period):
    """Calculate EMA"""
    multiplier = 2 / (period + 1)
    ema = np.mean(prices[:period])
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calculate_bb_position(prices, period=20):
    """Calculate Bollinger Band position"""
    if len(prices) < period:
        return 50
    
    recent = prices[-period:]
    sma = np.mean(recent)
    std = np.std(recent)
    
    upper = sma + (2 * std)
    lower = sma - (2 * std)
    current = prices[-1]
    
    if upper == lower:
        return 50
    
    position = ((current - lower) / (upper - lower)) * 100
    return max(0, min(100, position))

def calculate_volume_multiple(volumes):
    """Calculate volume multiple"""
    if len(volumes) < 20:
        return 1.0
    
    current = volumes[-1]
    avg20 = np.mean(volumes[-20:])
    
    if avg20 == 0:
        return 1.0
    
    return current / avg20

def detect_trend(prices):
    """Detect trend"""
    if len(prices) < 5:
        return 'Sideways'
    
    recent = prices[-5:]
    ups = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i-1])
    
    if ups >= 3:
        return 'Uptrend'
    elif ups <= 1:
        return 'Downtrend'
    else:
        return 'Sideways'

def analyze_stock(data):
    """Analyze stock and generate score"""
    if not data:
        return None
    
    price = data['price']
    change = data['change']
    rsi = data['rsi']
    macd = data['macd']
    bb = data['bb_position']
    vol = data['vol_multiple']
    trend = data['trend']
    
    # Calculate potential
    potential_rs = max(20, price * 0.05)
    potential_pct = (potential_rs / price) * 100
    
    score = 0
    criteria = []
    
    # Criterion 1: Potential (15 points)
    if potential_rs >= 20 and potential_pct >= 5:
        score += 15
        criteria.append('✅ Potential ≥₹20 & ≥5%')
    elif potential_rs >= 20:
        score += 10
        criteria.append('✅ Potential ≥₹20')
    else:
        criteria.append('❌ Low potential')
    
    # Criterion 2: RSI (20 points)
    if 50 <= rsi < 70:
        score += 20
        criteria.append(f'✅ RSI Bullish ({rsi:.0f})')
    elif 30 <= rsi < 50:
        score += 15
        criteria.append(f'✅ RSI Building ({rsi:.0f})')
    elif rsi >= 70:
        score += 10
        criteria.append(f'⚠️ RSI Overbought ({rsi:.0f})')
    else:
        score += 5
        criteria.append(f'❌ RSI Weak ({rsi:.0f})')
    
    # Criterion 3: MACD (15 points)
    if macd > 0:
        score += 15
        criteria.append('✅ MACD Bullish')
    elif macd > -5:
        score += 10
        criteria.append('✅ MACD Improving')
    else:
        score += 5
        criteria.append('❌ MACD Bearish')
    
    # Criterion 4: Bollinger Bands (15 points)
    if 20 <= bb <= 40:
        score += 15
        criteria.append(f'✅ BB Lower ({bb:.0f}%)')
    elif 50 <= bb <= 70:
        score += 12
        criteria.append(f'✅ BB Upper ({bb:.0f}%)')
    elif 40 < bb < 50:
        score += 10
        criteria.append(f'✅ BB Middle ({bb:.0f}%)')
    else:
        score += 5
        criteria.append(f'⚠️ BB Extreme ({bb:.0f}%)')
    
    # Criterion 5: Volume (15 points)
    if vol >= 2.0:
        score += 15
        criteria.append(f'✅ Volume Surge ({vol:.1f}x)')
    elif vol >= 1.5:
        score += 12
        criteria.append(f'✅ Volume Above Avg ({vol:.1f}x)')
    elif vol >= 1.2:
        score += 8
        criteria.append(f'✅ Volume Increasing ({vol:.1f}x)')
    else:
        score += 5
        criteria.append(f'❌ Volume Normal ({vol:.1f}x)')
    
    # Criterion 6: Trend (10 points)
    if trend == 'Uptrend':
        score += 10
        criteria.append('✅ Uptrend')
    elif trend == 'Sideways':
        score += 5
        criteria.append('⚠️ Sideways')
    else:
        criteria.append('❌ Downtrend')
    
    # Criterion 7: Daily Change (10 points)
    if change > 3:
        score += 10
        criteria.append(f'✅ Strong Day (+{change:.1f}%)')
    elif change > 1:
        score += 8
        criteria.append(f'✅ Positive Day (+{change:.1f}%)')
    elif change > 0:
        score += 5
        criteria.append(f'✅ Slight Gain (+{change:.1f}%)')
    elif change > -2:
        score += 3
        criteria.append(f'⚠️ Small Loss ({change:.1f}%)')
    else:
        criteria.append(f'❌ Declining ({change:.1f}%)')
    
    # Qualification
    qualified = score >= 60
    
    if score >= 90:
        status = '🌟 Excellent'
        status_class = 'qualified'
    elif score >= 80:
        status = '✅ Very Good'
        status_class = 'qualified'
    elif score >= 70:
        status = '✅ Good'
        status_class = 'qualified'
    elif score >= 60:
        status = '✅ Fair'
        status_class = 'qualified'
    elif score >= 50:
        status = '⚠️ Watchlist'
        status_class = 'watchlist'
    else:
        status = '❌ Not Qualified'
        status_class = 'not-qualified'
    
    met_count = len([c for c in criteria if '✅' in c])
    
    return {
        'symbol': data['symbol'],
        'price': price,
        'change': change,
        'potential_rs': potential_rs,
        'potential_pct': potential_pct,
        'rsi': rsi,
        'macd': macd,
        'bb': bb,
        'vol': vol,
        'trend': trend,
        'score': score,
        'qualified': qualified,
        'status': status,
        'status_class': status_class,
        'criteria': criteria,
        'met_count': met_count,
        'sector': SECTOR_MAP.get(data['symbol'], 'Other')
    }

# Main App
st.markdown('<p class="main-header">🎯 Indian Stock Scout - LIVE Scanner</p>', unsafe_allow_html=True)
st.markdown("**Comprehensive real-time analysis with Yahoo Finance data**")

# Sidebar
st.sidebar.header("⚙️ Configuration")

scan_mode = st.sidebar.radio("Scan Mode", ["Quick Scan (Top 30)", "Full Scan (All Stocks)", "Custom List"])

if scan_mode == "Quick Scan (Top 30)":
    stocks_to_scan = NSE_STOCKS[:30]
elif scan_mode == "Full Scan (All Stocks)":
    stocks_to_scan = NSE_STOCKS
else:
    custom_input = st.sidebar.text_area("Enter symbols (one per line)", "RELIANCE\nTCS\nINFY")
    stocks_to_scan = [s.strip().upper() for s in custom_input.split('\n') if s.strip()]

min_score = st.sidebar.slider("Minimum Score", 0, 100, 60, 5)
show_all = st.sidebar.checkbox("Show all stocks (including non-qualified)", False)

if st.sidebar.button("🚀 START LIVE SCAN", type="primary", use_container_width=True):
    st.markdown("---")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    total = len(stocks_to_scan)
    
    for idx, symbol in enumerate(stocks_to_scan):
        status_text.info(f"📊 Fetching {symbol}... ({idx+1}/{total})")
        
        data = fetch_stock_data(symbol)
        if data:
            analysis = analyze_stock(data)
            if analysis:
                results.append(analysis)
        
        progress_bar.progress((idx + 1) / total)
        time.sleep(0.1)  # Rate limiting
    
    status_text.success(f"✅ Scan complete! Analyzed {len(results)} stocks")
    time.sleep(1)
    status_text.empty()
    progress_bar.empty()
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Filter
    if not show_all:
        results = [r for r in results if r['score'] >= min_score]
    
    # Statistics
    st.markdown("---")
    st.subheader("📊 Scan Statistics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    qualified = [r for r in results if r['qualified']]
    watchlist = [r for r in results if 50 <= r['score'] < 60]
    below_par = [r for r in results if r['score'] < 50]
    
    col1.metric("Total Scanned", total)
    col2.metric("Qualified (≥60)", len(qualified))
    col3.metric("Watchlist (50-59)", len(watchlist))
    col4.metric("Below Par (<50)", len(below_par))
    
    if results:
        avg_score = sum(r['score'] for r in results) / len(results)
        col5.metric("Avg Score", f"{avg_score:.1f}")
    
    # Results
    st.markdown("---")
    st.subheader(f"📈 Results ({len(results)} stocks)")
    
    if not results:
        st.warning("No stocks found matching criteria")
    else:
        # Display each result
        for result in results:
            with st.expander(f"{result['status']} - {result['symbol']} | Score: {result['score']} | Price: ₹{result['price']:.2f}", expanded=False):
                st.markdown(f'<div class="{result["status_class"]}">', unsafe_allow_html=True)
                
                # Key metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Price", f"₹{result['price']:.2f}")
                col2.metric("Change", f"{result['change']:.2f}%", delta=f"{result['change']:.2f}%")
                col3.metric("Score", result['score'])
                col4.metric("Potential", f"₹{result['potential_rs']:.2f}")
                col5.metric("Sector", result['sector'])
                
                # Technical indicators
                st.markdown("**Technical Indicators:**")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("RSI", f"{result['rsi']:.1f}")
                col2.metric("MACD", "Bullish" if result['macd'] > 0 else "Bearish")
                col3.metric("BB Position", f"{result['bb']:.0f}%")
                col4.metric("Volume", f"{result['vol']:.1f}x")
                
                # Criteria breakdown
                st.markdown("**Criteria Analysis:**")
                st.markdown(f"Met **{result['met_count']}/7** criteria")
                for criterion in result['criteria']:
                    st.markdown(f"- {criterion}")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Download results
        st.markdown("---")
        st.subheader("💾 Download Results")
        
        df = pd.DataFrame([{
            'Symbol': r['symbol'],
            'Price': r['price'],
            'Change %': r['change'],
            'Potential ₹': r['potential_rs'],
            'Potential %': r['potential_pct'],
            'RSI': r['rsi'],
            'MACD': 'Bullish' if r['macd'] > 0 else 'Bearish',
            'BB Position': r['bb'],
            'Volume Multiple': r['vol'],
            'Trend': r['trend'],
            'Score': r['score'],
            'Qualified': 'YES' if r['qualified'] else 'NO',
            'Status': r['status'],
            'Sector': r['sector'],
            'Met Criteria': r['met_count']
        } for r in results])
        
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            f"stock_scout_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True
        )

else:
    st.info("👈 Configure your scan settings and click 'START LIVE SCAN'")
    
    st.markdown("---")
    st.subheader("📋 Scanning Criteria")
    
    st.markdown("""
    **This scanner analyzes 7 key criteria:**
    
    1. **Price Potential** (15 pts) - Stock must have ≥₹20 or ≥5% move potential
    2. **RSI** (20 pts) - Momentum indicator (optimal: 50-70)
    3. **MACD** (15 pts) - Trend momentum (bullish preferred)
    4. **Bollinger Bands** (15 pts) - Position analysis (oversold zones favored)
    5. **Volume** (15 pts) - Trading activity (≥1.5x average preferred)
    6. **Trend** (10 pts) - Price pattern (uptrend preferred)
    7. **Daily Performance** (10 pts) - Current session momentum
    
    **Qualification:** Score ≥60 = QUALIFIED | 50-59 = WATCHLIST | <50 = NOT QUALIFIED
    """)
    
    st.markdown("---")
    st.subheader("💡 Usage Tips")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Scan Modes:**
        - **Quick Scan**: Top 30 liquid stocks (faster)
        - **Full Scan**: All 90+ stocks (comprehensive)
        - **Custom List**: Your specific watchlist
        """)
    
    with col2:
        st.markdown("""
        **Best Practices:**
        - Run scans during market hours for real-time data
        - Use Quick Scan for daily checks
        - Use Full Scan for weekly deep dives
        - Download results for tracking
        """)

st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#666;'>
<p>Built with Streamlit | Real data via Yahoo Finance (yfinance)</p>
<p style='font-size:0.85rem;'>⚠️ For educational purposes only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)
