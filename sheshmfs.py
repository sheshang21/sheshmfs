import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import time
import io

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Indian Stock Scout - LIVE Scanner", page_icon="🎯", layout="wide")

# Custom CSS
st.markdown("""<style>
.main-header{font-size:2.5rem;font-weight:700;color:#1f77b4;text-align:center;margin-bottom:1rem}
.sub-header{font-size:1.5rem;font-weight:600;color:#333;margin:1rem 0}
.metric-card{background:#f8f9fb;padding:0.8rem;border-radius:8px;border-left:4px solid #1f77b4;margin:0.5rem 0}
.stDataFrame{font-size:0.9rem}
div[data-testid="stDataFrame"] > div{background:#f8f9fb}
</style>""", unsafe_allow_html=True)

# Comprehensive Stock Universe - 200+ NSE Stocks
NSE_STOCKS = [
    # Nifty 50
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC', 'SBIN', 
    'BHARTIARTL', 'KOTAKBANK', 'LT', 'AXISBANK', 'ASIANPAINT', 'MARUTI', 'HCLTECH',
    'BAJFINANCE', 'WIPRO', 'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'ONGC',
    'TATAMOTORS', 'NTPC', 'POWERGRID', 'JSWSTEEL', 'M&M', 'TECHM', 'ADANIENT', 'ADANIPORTS',
    'COALINDIA', 'HINDALCO', 'TATASTEEL', 'BAJAJFINSV', 'DIVISLAB', 'DRREDDY', 'GRASIM',
    'CIPLA', 'BRITANNIA', 'EICHERMOT', 'HEROMOTOCO', 'APOLLOHOSP', 'INDUSINDBK', 'UPL',
    'BPCL', 'SBILIFE', 'HDFCLIFE', 'BAJAJ-AUTO', 'VEDL', 'TATACONSUM',
    # Nifty Next 50 & High Volume Stocks
    'ADANIGREEN', 'GODREJCP', 'DABUR', 'PIDILITIND', 'HAVELLS', 'BERGEPAINT', 'SIEMENS',
    'AMBUJACEM', 'DLF', 'INDIGO', 'BANDHANBNK', 'CHOLAFIN', 'GAIL', 'BOSCHLTD',
    'MUTHOOTFIN', 'MARICO', 'SAIL', 'AUROPHARMA', 'NMDC', 'TATAPOWER', 'LUPIN',
    'ZYDUSLIFE', 'PETRONET', 'PNB', 'BANKBARODA', 'RECLTD', 'CANBK', 'IRCTC',
    'BEL', 'HAL', 'HFCL', 'ZEEL', 'INDUSTOWER', 'YESBANK', 'DIXON', 'TRENT',
    'DMART', 'NAUKRI', 'ZOMATO', 'PAYTM', 'PFC', 'MOTHERSON', 'ESCORTS', 'ASHOKLEY',
    'TVSMOTOR', 'BALKRISIND', 'MRF', 'APOLLOTYRE', 'CEAT', 'JUBLFOOD',
    # Mid & Small Cap High Activity
    'PAGEIND', 'IGL', 'MGL', 'TORNTPOWER', 'TORNTPHARM', 'LICI', 'ABFRL', 'VOLTAS', 
    'PERSISTENT', 'COFORGE', 'LTIM', 'MPHASIS', 'OFSS', 'IRFC', 'RVNL', 'TIINDIA', 
    'TATAELXSI', 'LTTS', 'BIOCON', 'ALKEM', 'POLYCAB', 'CUMMINSIND', 'ABB', 'THERMAX', 
    'SHREECEM', 'RAMCOCEM', 'JKCEMENT', 'WHIRLPOOL', 'CROMPTON', 'BATAINDIA', 'RELAXO', 
    'VBL', 'COLPAL', 'GILLETTE', 'HONAUT', 'SCHAEFFLER', 'FEDERALBNK', 'IDFCFIRSTB', 
    'AUBANK', 'INDHOTEL', 'INDIANB', 'IOB', 'UNIONBANK', 'SYNGENE', 'CONCOR',
    'ADANIPOWER', 'ADANITRANS', 'ATGL', 'JSWENERGY', 'NHPC', 'SJVN', 'PRESTIGE',
    'OBEROIRLTY', 'PHOENIXLTD', 'IPCALAB', 'ABBOTINDIA', 'GLAXO', 'PFIZER', 'SANOFI',
    'LAURUSLABS', 'ICICIGI', 'ICICIPRULI', 'SBICARD', 'RBLBANK', 'LICHSGFIN',
    'AARTIIND', 'DEEPAKNI', 'GNFC', 'CHAMBLFERT', 'COROMANDEL', 'PIIND', 'NAVINFLUOR',
    'SRF', 'ATUL', 'FLUOROCHEM', 'CLEAN', 'GRSE', 'MAZAGON', 'COCHINSHIP', 'BHARATFORG',
    'AIAENG', 'CRISIL', 'CREDITACC', 'IIFL', 'MANAPPURAM', 'LTF', 'SHRIRAMFIN',
    'SRTRANSFIN', 'PEL', 'BLUESTARCO', 'VGUARD', 'KEI', 'APLAPOLLO', 'JINDALSTEL',
    'RATNAMANI', 'GMRINFRA', 'ADANIENSOL', 'SUZLON', 'IREDA', 'CUB', 'DELTACORP',
    'PVR', 'INOXLEISUR', 'FINEORG', 'DALBHARAT', 'CENTURYTEX', 'RAYMOND', 'GUJGAS',
    'MSUMI', 'EXIDEIND', 'PGHH', 'METROPOLIS', 'KPITTECH', 'MCDOWELL-N', 'TATACOMM',
    'IDEA', 'ASTRAL', 'KALYANKJIL', 'SUPREMEIND', 'SONACOMS', 'NAVNETEDUL', 'Route'
]

SECTOR_MAP = {
    'RELIANCE': 'Energy', 'TCS': 'IT', 'HDFCBANK': 'Banking', 'INFY': 'IT', 'ICICIBANK': 'Banking',
    'HINDUNILVR': 'FMCG', 'ITC': 'FMCG', 'SBIN': 'Banking', 'BHARTIARTL': 'Telecom', 'KOTAKBANK': 'Banking',
    'LT': 'Infrastructure', 'AXISBANK': 'Banking', 'ASIANPAINT': 'Paints', 'MARUTI': 'Auto', 'HCLTECH': 'IT',
    'BAJFINANCE': 'NBFC', 'WIPRO': 'IT', 'SUNPHARMA': 'Pharma', 'TITAN': 'Consumer', 'ULTRACEMCO': 'Cement',
    'NESTLEIND': 'FMCG', 'ONGC': 'Energy', 'TATAMOTORS': 'Auto', 'NTPC': 'Power', 'POWERGRID': 'Power',
    'JSWSTEEL': 'Metals', 'M&M': 'Auto', 'TECHM': 'IT', 'ADANIENT': 'Conglomerate', 'ADANIPORTS': 'Infrastructure',
    'COALINDIA': 'Mining', 'HINDALCO': 'Metals', 'TATASTEEL': 'Metals', 'BAJAJFINSV': 'NBFC', 'DIVISLAB': 'Pharma',
    'DRREDDY': 'Pharma', 'GRASIM': 'Diversified', 'CIPLA': 'Pharma', 'BRITANNIA': 'FMCG', 'EICHERMOT': 'Auto',
    'HEROMOTOCO': 'Auto', 'APOLLOHOSP': 'Healthcare', 'INDUSINDBK': 'Banking', 'UPL': 'Chemicals',
    'BPCL': 'Energy', 'SBILIFE': 'Insurance', 'HDFCLIFE': 'Insurance', 'BAJAJ-AUTO': 'Auto',
    'VEDL': 'Metals', 'TATACONSUM': 'FMCG', 'ADANIGREEN': 'Renewable', 'GODREJCP': 'FMCG',
    'DABUR': 'FMCG', 'PIDILITIND': 'Chemicals', 'HAVELLS': 'Electricals', 'BERGEPAINT': 'Paints',
    'SIEMENS': 'Engineering', 'AMBUJACEM': 'Cement', 'DLF': 'Realty', 'INDIGO': 'Aviation',
    'BANDHANBNK': 'Banking', 'CHOLAFIN': 'NBFC', 'GAIL': 'Energy', 'BOSCHLTD': 'Auto Parts',
    'MUTHOOTFIN': 'NBFC', 'MARICO': 'FMCG', 'SAIL': 'Metals', 'AUROPHARMA': 'Pharma',
    'NMDC': 'Mining', 'TATAPOWER': 'Power', 'LUPIN': 'Pharma', 'ZYDUSLIFE': 'Pharma',
    'PETRONET': 'Energy', 'PNB': 'Banking', 'BANKBARODA': 'Banking', 'RECLTD': 'NBFC',
    'CANBK': 'Banking', 'IRCTC': 'Tourism', 'BEL': 'Defense', 'HAL': 'Defense',
    'HFCL': 'Telecom', 'ZEEL': 'Media', 'INDUSTOWER': 'Telecom', 'YESBANK': 'Banking',
    'DIXON': 'Electronics', 'TRENT': 'Retail', 'DMART': 'Retail', 'NAUKRI': 'Internet',
    'ZOMATO': 'Internet', 'PAYTM': 'Fintech', 'PFC': 'NBFC', 'MOTHERSON': 'Auto Parts',
    'ESCORTS': 'Auto', 'ASHOKLEY': 'Auto', 'TVSMOTOR': 'Auto', 'BALKRISIND': 'Auto Parts',
    'MRF': 'Auto Parts', 'APOLLOTYRE': 'Auto Parts', 'CEAT': 'Auto Parts', 'JUBLFOOD': 'Food',
    'PAGEIND': 'FMCG', 'IGL': 'Energy', 'MGL': 'Energy', 'TORNTPOWER': 'Power',
    'TORNTPHARM': 'Pharma', 'LICI': 'Insurance', 'ABFRL': 'Retail', 'VOLTAS': 'Engineering',
    'PERSISTENT': 'IT', 'COFORGE': 'IT', 'LTIM': 'IT', 'MPHASIS': 'IT', 'OFSS': 'IT',
    'IRFC': 'NBFC', 'RVNL': 'Infrastructure', 'TIINDIA': 'Metals', 'TATAELXSI': 'IT',
    'LTTS': 'IT', 'BIOCON': 'Pharma', 'ALKEM': 'Pharma', 'POLYCAB': 'Cables',
    'CUMMINSIND': 'Engineering', 'ABB': 'Engineering', 'THERMAX': 'Engineering',
    'SHREECEM': 'Cement', 'RAMCOCEM': 'Cement', 'JKCEMENT': 'Cement', 'WHIRLPOOL': 'Consumer',
    'CROMPTON': 'Electricals', 'BATAINDIA': 'Footwear', 'RELAXO': 'Footwear',
    'VBL': 'Beverages', 'COLPAL': 'FMCG', 'GILLETTE': 'FMCG', 'HONAUT': 'Engineering',
    'SCHAEFFLER': 'Auto Parts', 'FEDERALBNK': 'Banking', 'IDFCFIRSTB': 'Banking',
    'AUBANK': 'Banking', 'INDHOTEL': 'Hospitality', 'INDIANB': 'Banking', 'IOB': 'Banking',
    'UNIONBANK': 'Banking', 'SYNGENE': 'Pharma', 'CONCOR': 'Logistics', 'ADANIPOWER': 'Power',
    'ADANITRANS': 'Infrastructure', 'ATGL': 'Energy', 'JSWENERGY': 'Power', 'NHPC': 'Power',
    'SJVN': 'Power', 'PRESTIGE': 'Realty', 'OBEROIRLTY': 'Realty', 'PHOENIXLTD': 'Realty',
    'IPCALAB': 'Pharma', 'ABBOTINDIA': 'Pharma', 'GLAXO': 'Pharma', 'PFIZER': 'Pharma',
    'SANOFI': 'Pharma', 'LAURUSLABS': 'Pharma', 'ICICIGI': 'Insurance', 'ICICIPRULI': 'Insurance',
    'SBICARD': 'NBFC', 'RBLBANK': 'Banking', 'LICHSGFIN': 'NBFC', 'AARTIIND': 'Chemicals',
    'DEEPAKNI': 'Chemicals', 'GNFC': 'Chemicals', 'CHAMBLFERT': 'Chemicals', 'COROMANDEL': 'Chemicals',
    'PIIND': 'Chemicals', 'NAVINFLUOR': 'Chemicals', 'SRF': 'Chemicals', 'ATUL': 'Chemicals',
    'FLUOROCHEM': 'Chemicals', 'CLEAN': 'Chemicals', 'GRSE': 'Defense', 'MAZAGON': 'Defense',
    'COCHINSHIP': 'Defense', 'BHARATFORG': 'Auto Parts', 'AIAENG': 'Auto Parts', 'CRISIL': 'Financial Services',
    'CREDITACC': 'Financial Services', 'IIFL': 'NBFC', 'MANAPPURAM': 'NBFC', 'LTF': 'NBFC'
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
st.markdown('<p class="main-header">🎯 Indian Stock Scout - LIVE Market Scanner</p>', unsafe_allow_html=True)
st.markdown("**Real-time NSE stock analysis with Yahoo Finance data**")

# Sidebar Configuration
st.sidebar.header("⚙️ Scanner Configuration")

scan_mode = st.sidebar.radio("Scan Mode", 
    ["Quick Scan (50 stocks)", "Full Scan (200+ stocks)", "Custom List"])

if scan_mode == "Quick Scan (50 stocks)":
    stocks_to_scan = NSE_STOCKS[:50]
    st.sidebar.info(f"Will scan: {len(stocks_to_scan)} stocks")
elif scan_mode == "Full Scan (200+ stocks)":
    stocks_to_scan = NSE_STOCKS
    st.sidebar.warning(f"Will scan: {len(stocks_to_scan)} stocks (may take 5-10 min)")
else:
    custom_input = st.sidebar.text_area("Enter NSE symbols (one per line)", 
        "RELIANCE\nTCS\nINFY\nHDFCBANK\nICICIBANK", height=150)
    stocks_to_scan = [s.strip().upper() for s in custom_input.split('\n') if s.strip()]
    st.sidebar.info(f"Will scan: {len(stocks_to_scan)} stocks")

st.sidebar.markdown("---")
st.sidebar.subheader("Criteria Settings")

min_score = st.sidebar.slider("Minimum Score", 0, 100, 60, 5,
    help="Only show stocks with score ≥ this value")

min_potential_rs = st.sidebar.number_input("Min Potential (₹)", 0, 100, 20, 5,
    help="Minimum rupee movement potential")

min_potential_pct = st.sidebar.number_input("Min Potential (%)", 0.0, 20.0, 5.0, 0.5,
    help="Minimum percentage movement potential")

st.sidebar.markdown("---")

# Session state for storing results
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None
    st.session_state.scan_timestamp = None

# Scan button
if st.sidebar.button("🚀 START LIVE SCAN", type="primary", use_container_width=True):
    st.markdown("---")
    st.subheader("📊 Scanning in Progress...")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    stats_placeholder = st.empty()
    
    results = []
    total = len(stocks_to_scan)
    failed = 0
    
    for idx, symbol in enumerate(stocks_to_scan):
        status_text.info(f"📊 Fetching **{symbol}**... ({idx+1}/{total})")
        
        data = fetch_stock_data(symbol)
        if data:
            analysis = analyze_stock(data)
            if analysis:
                results.append(analysis)
        else:
            failed += 1
        
        # Update progress
        progress = (idx + 1) / total
        progress_bar.progress(progress)
        
        # Show interim stats
        if (idx + 1) % 10 == 0 or idx == total - 1:
            qualified_count = len([r for r in results if r['qualified']])
            stats_placeholder.info(f"✅ Analyzed: {len(results)} | Qualified: {qualified_count} | Failed: {failed}")
        
        time.sleep(0.15)  # Rate limiting
    
    # Store results in session state
    st.session_state.scan_results = results
    st.session_state.scan_timestamp = datetime.now()
    
    status_text.success(f"✅ Scan complete! Analyzed {len(results)}/{total} stocks")
    time.sleep(1)
    status_text.empty()
    stats_placeholder.empty()
    progress_bar.empty()
    
    st.rerun()

# Display results if available
if st.session_state.scan_results:
    results = st.session_state.scan_results
    scan_time = st.session_state.scan_timestamp
    
    st.markdown("---")
    st.subheader(f"📈 Scan Results")
    st.caption(f"Scanned at: {scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'Symbol': r['symbol'],
        'Price (₹)': r['price'],
        'Change (%)': r['change'],
        'Potential (₹)': r['potential_rs'],
        'Potential (%)': r['potential_pct'],
        'RSI': r['rsi'],
        'MACD': 'Bullish' if r['macd'] > 0 else 'Bearish',
        'BB Position (%)': r['bb'],
        'Vol Multiple': r['vol'],
        'Trend': r['trend'],
        'Score': r['score'],
        'Qualified': 'YES' if r['qualified'] else 'NO',
        'Status': r['status'],
        'Sector': r['sector'],
        'Met Criteria': r['met_count']
    } for r in results])
    
    # Statistics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    qualified = df[df['Qualified'] == 'YES']
    watchlist = df[(df['Score'] >= 50) & (df['Score'] < 60)]
    below_par = df[df['Score'] < 50]
    
    col1.metric("Total Scanned", len(df))
    col2.metric("Qualified (≥60)", len(qualified))
    col3.metric("Watchlist (50-59)", len(watchlist))
    col4.metric("Below Par (<50)", len(below_par))
    col5.metric("Avg Score", f"{df['Score'].mean():.1f}")
    col6.metric("Top Score", f"{df['Score'].max()}")
    
    st.markdown("---")
    
    # Filtering options
    st.subheader("🔍 Filter & Sort Results")
    
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    
    with filter_col1:
        filter_qualified = st.selectbox("Qualification", 
            ["All", "Qualified Only", "Watchlist", "Below Par"])
    
    with filter_col2:
        filter_sector = st.selectbox("Sector", 
            ["All"] + sorted(df['Sector'].unique().tolist()))
    
    with filter_col3:
        filter_trend = st.selectbox("Trend", 
            ["All", "Uptrend", "Sideways", "Downtrend"])
    
    with filter_col4:
        filter_macd = st.selectbox("MACD", 
            ["All", "Bullish", "Bearish"])
    
    # Apply filters
    filtered_df = df.copy()
    
    if filter_qualified == "Qualified Only":
        filtered_df = filtered_df[filtered_df['Qualified'] == 'YES']
    elif filter_qualified == "Watchlist":
        filtered_df = filtered_df[(filtered_df['Score'] >= 50) & (filtered_df['Score'] < 60)]
    elif filter_qualified == "Below Par":
        filtered_df = filtered_df[filtered_df['Score'] < 50]
    
    if filter_sector != "All":
        filtered_df = filtered_df[filtered_df['Sector'] == filter_sector]
    
    if filter_trend != "All":
        filtered_df = filtered_df[filtered_df['Trend'] == filter_trend]
    
    if filter_macd != "All":
        filtered_df = filtered_df[filtered_df['MACD'] == filter_macd]
    
    # Additional numeric filters
    filter_col5, filter_col6 = st.columns(2)
    with filter_col5:
        filter_min_score = st.number_input("Min Score", 0, 100, min_score, 5)
        filtered_df = filtered_df[filtered_df['Score'] >= filter_min_score]
    
    with filter_col6:
        filter_min_potential = st.number_input("Min Potential (₹)", 0.0, 100.0, float(min_potential_rs))
        filtered_df = filtered_df[filtered_df['Potential (₹)'] >= filter_min_potential]
    
    st.markdown("---")
    
    # Display filtered count
    st.info(f"📊 Showing **{len(filtered_df)}** stocks (filtered from {len(df)} total)")
    
    # Main data table with color coding
    st.subheader("📋 Stock Analysis Table")
    
    # Apply styling
    def highlight_qualified(row):
        if row['Score'] >= 80:
            return ['background-color: #d4edda'] * len(row)
        elif row['Score'] >= 60:
            return ['background-color: #d1ecf1'] * len(row)
        elif row['Score'] >= 50:
            return ['background-color: #fff3cd'] * len(row)
        else:
            return ['background-color: #f8d7da'] * len(row)
    
    styled_df = filtered_df.style.apply(highlight_qualified, axis=1)\
        .format({
            'Price (₹)': '₹{:.2f}',
            'Change (%)': '{:+.2f}%',
            'Potential (₹)': '₹{:.2f}',
            'Potential (%)': '{:.2f}%',
            'RSI': '{:.1f}',
            'BB Position (%)': '{:.0f}%',
            'Vol Multiple': '{:.2f}x'
        })
    
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    st.markdown("---")
    
    # Detailed view section
    st.subheader("🔍 Detailed Stock Analysis")
    
    if len(filtered_df) > 0:
        selected_symbol = st.selectbox("Select a stock for detailed view", 
            filtered_df['Symbol'].tolist())
        
        # Find the detailed result
        selected_result = next((r for r in results if r['symbol'] == selected_symbol), None)
        
        if selected_result:
            st.markdown(f"### {selected_symbol} - {selected_result['status']}")
            
            # Key metrics in columns
            met_col1, met_col2, met_col3, met_col4, met_col5 = st.columns(5)
            met_col1.metric("Score", selected_result['score'])
            met_col2.metric("Price", f"₹{selected_result['price']:.2f}")
            met_col3.metric("Change", f"{selected_result['change']:.2f}%")
            met_col4.metric("Potential", f"₹{selected_result['potential_rs']:.2f}")
            met_col5.metric("Sector", selected_result['sector'])
            
            # Technical indicators
            st.markdown("#### Technical Indicators")
            tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)
            tech_col1.metric("RSI", f"{selected_result['rsi']:.1f}")
            tech_col2.metric("MACD", "🟢 Bullish" if selected_result['macd'] > 0 else "🔴 Bearish")
            tech_col3.metric("BB Position", f"{selected_result['bb']:.0f}%")
            tech_col4.metric("Volume", f"{selected_result['vol']:.2f}x")
            
            # Criteria breakdown
            st.markdown("#### Criteria Breakdown")
            st.markdown(f"**Met {selected_result['met_count']} out of 7 criteria**")
            
            for criterion in selected_result['criteria']:
                if '✅' in criterion:
                    st.success(criterion)
                elif '⚠️' in criterion:
                    st.warning(criterion)
                else:
                    st.error(criterion)
    
    st.markdown("---")
    
    # Download options
    st.subheader("💾 Download Options")
    
    download_col1, download_col2, download_col3 = st.columns(3)
    
    with download_col1:
        # Full detailed CSV
        detailed_csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Results (CSV)",
            data=detailed_csv,
            file_name=f"stock_scout_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with download_col2:
        # Complete results with all stocks
        complete_csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download All Results (CSV)",
            data=complete_csv,
            file_name=f"stock_scout_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with download_col3:
        # Excel format with multiple sheets (optional - requires openpyxl)
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, sheet_name='Filtered Results', index=False)
                df.to_excel(writer, sheet_name='All Results', index=False)
                
                # Summary sheet
                summary_data = {
                    'Metric': ['Total Scanned', 'Qualified', 'Watchlist', 'Below Par', 
                              'Avg Score', 'Top Score', 'Scan Time'],
                    'Value': [len(df), len(qualified), len(watchlist), len(below_par),
                             f"{df['Score'].mean():.1f}", df['Score'].max(),
                             scan_time.strftime('%Y-%m-%d %H:%M:%S')]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            st.download_button(
                label="📥 Download Excel (Multi-sheet)",
                data=buffer.getvalue(),
                file_name=f"stock_scout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except ImportError:
            st.warning("Excel export requires openpyxl. Install with: pip install openpyxl")
            # Fallback to CSV
            st.download_button(
                label="📥 Download Backup CSV",
                data=complete_csv,
                file_name=f"stock_scout_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

else:
    # Initial state - no scan run yet
    st.info("👈 Configure your scan settings in the sidebar and click **'START LIVE SCAN'** to begin")
    
    st.markdown("---")
    st.subheader("📋 About This Scanner")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🎯 What This Scanner Does:**
        
        - Fetches **real-time data** from Yahoo Finance
        - Analyzes stocks using **7 technical criteria**
        - Scores each stock from **0-100 points**
        - Identifies stocks with **≥₹20 or ≥5% potential**
        - Shows which criteria each stock meets
        - Provides **sortable, filterable tables**
        - Exports data to **CSV and Excel**
        """)
    
    with col2:
        st.markdown("""
        **📊 Scoring Criteria (100 points total):**
        
        1. **Price Potential** (15 pts) - ≥₹20 or ≥5% movement
        2. **RSI** (20 pts) - Momentum indicator (50-70 optimal)
        3. **MACD** (15 pts) - Trend momentum
        4. **Bollinger Bands** (15 pts) - Volatility position
        5. **Volume** (15 pts) - Trading activity (≥1.5x avg)
        6. **Trend** (10 pts) - Up/Down/Sideways pattern
        7. **Daily Change** (10 pts) - Current session performance
        """)
    
    st.markdown("---")
    st.subheader("🎓 Qualification Levels")
    
    qual_col1, qual_col2, qual_col3, qual_col4 = st.columns(4)
    
    with qual_col1:
        st.success("""
        **✅ QUALIFIED**
        
        Score: 60-100
        
        Meets most criteria
        """)
    
    with qual_col2:
        st.warning("""
        **⚠️ WATCHLIST**
        
        Score: 50-59
        
        Monitor closely
        """)
    
    with qual_col3:
        st.error("""
        **❌ BELOW PAR**
        
        Score: 0-49
        
        Multiple issues
        """)
    
    with qual_col4:
        st.info("""
        **🌟 EXCELLENT**
        
        Score: 80-100
        
        Strong signals
        """)
    
    st.markdown("---")
    st.subheader("💡 Pro Tips")
    
    st.markdown("""
    - **Quick Scan (50 stocks)**: Best for daily monitoring, takes ~2-3 minutes
    - **Full Scan (200+ stocks)**: Comprehensive analysis, takes ~8-10 minutes  
    - **Custom List**: Analyze your specific watchlist
    - **Run during market hours** for most accurate real-time data
    - **Use filters** after scanning to find specific opportunities
    - **Download results** to track performance over time
    """)

st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#666;'>
<p><strong>Indian Stock Scout</strong> | Built with Streamlit & yfinance</p>
<p style='font-size:0.85rem;'>⚠️ For educational purposes only. Not financial advice. Do your own research.</p>
</div>
""", unsafe_allow_html=True)
