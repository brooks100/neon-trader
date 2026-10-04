# ============================================================
#  NEON TRADER v2  -  GBP 1000 BANK  -  DEPLOY-READY
#  Persistent wallet (survives restarts). Paper trading.
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import requests
import urllib.parse
import json
import os
from datetime import datetime

# ---------------- SETTINGS ----------------
DEFAULT_BANK = 1000.0
FEE = 0.001
MAX_POSITIONS = 3
RISK_PER_TRADE = 0.33
STOP_LOSS_PCT = 0.03
TAKE_PROFIT_PCT = 0.06
REFRESH_SECONDS = 30
WALLET_FILE = os.path.join("data", "wallet.json")

ALL_COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
             "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]
STRATEGIES = ["AI Confluence (best setups)", "EMA Crossover",
              "RSI Mean Reversion", "MACD Momentum", "Bollinger Breakout"]

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"
BINANCE_PRICE = "https://api.binance.com/api/v3/ticker/price"

# ---------------- PERSISTENCE ----------------
def save_wallet():
    os.makedirs("data", exist_ok=True)
    payload = {
        "cash": st.session_state.cash,
        "positions": st.session_state.positions,
        "trades": st.session_state.trades,
        "equity": st.session_state.equity,
        "last_prices": st.session_state.last_prices,
        "alerts": st.session_state.alerts,
    }
    try:
        with open(WALLET_FILE, "w") as f:
            json.dump(payload, f)
    except Exception:
        pass

def load_wallet():
    if os.path.exists(WALLET_FILE):
        try:
            with open(WALLET_FILE, "r") as f:
                d = json.load(f)
            st.session_state.cash = d.get("cash", DEFAULT_BANK)
            st.session_state.positions = d.get("positions", {})
            st.session_state.trades = d.get("trades", [])
            st.session_state.equity = d.get("equity", [])
            st.session_state.last_prices = d.get("last_prices", {})
            st.session_state.alerts = d.get("alerts", [])
            return True
        except Exception:
            return False
    return False

def init_wallet():
    if not load_wallet():
        st.session_state.cash = DEFAULT_BANK
        st.session_state.positions = {}
        st.session_state.trades = []
        st.session_state.equity = []
        st.session_state.last_prices = {}
        st.session_state.alerts = [
            {"time": datetime.now().strftime("%H:%M:%S"), "type": "info",
             "text": f"Agent initialised with GBP {DEFAULT_BANK:.2f} virtual bank. Watching markets..."}
        ]
        save_wallet()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="NEON TRADER", page_icon="⚡", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@500;700;900&display=swap');
    .stApp { background: radial-gradient(ellipse at top, #0d0221 0%, #05010f 50%, #000000 100%); color:#e0f7ff; font-family:'Share Tech Mono',monospace; }
    #MainMenu, footer, .stDeployButton { visibility:hidden; display:none; }
    .stApp::before { content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
        background-image: linear-gradient(rgba(0,240,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,240,255,0.04) 1px, transparent 1px);
        background-size: 40px 40px; }
    h1,h2,h3 { font-family:'Orbitron',sans-serif !important; letter-spacing:2px; }
    .neon-header { text-align:center; padding:26px; margin-bottom:18px; border:1px solid rgba(0,240,255,0.4);
        border-radius:14px; background:rgba(0,240,255,0.04); box-shadow:0 0 30px rgba(0,240,255,0.15), inset 0 0 30px rgba(0,240,255,0.05); }
    .neon-header h1 { font-size:44px; font-weight:900; margin:0; color:#00f0ff;
        text-shadow:0 0 10px #00f0ff, 0 0 30px #00f0ff, 0 0 60px #0088ff; }
    .neon-header .sub { color:#ff2bd6; text-shadow:0 0 8px #ff2bd6; margin-top:6px; letter-spacing:3px; font-size:13px; }
    .status-chip { display:inline-block; margin-top:12px; padding:5px 16px; border-radius:20px; font-size:12px;
        letter-spacing:2px; font-weight:bold; border:1px solid #39ff14; color:#39ff14; background:rgba(57,255,20,0.08);
        box-shadow:0 0 12px rgba(57,255,20,0.4); animation: pulse 1.5s infinite; }
    @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.5;} }
    div[data-testid="stMetric"] { background:rgba(0,0,0,0.5); border:1px solid rgba(0,240,255,0.3);
        border-radius:10px; padding:14px; box-shadow:0 0 15px rgba(0,240,255,0.1); }
    div[data-testid="stMetricLabel"] p { color:#00f0ff !important; font-size:10px !important; letter-spacing:2px;
        text-transform:uppercase; font-family:'Orbitron',sans-serif; }
    div[data-testid="stMetricValue"] { color:#fff !important; font-family:'Share Tech Mono',monospace;
        font-size:26px !important; text-shadow:0 0 8px rgba(0,240,255,0.6); }
    .stButton>button { background:linear-gradient(90deg,#00f0ff,#ff2bd6); color:#000; font-weight:900;
        font-family:'Orbitron',sans-serif; letter-spacing:1px; border:none; border-radius:8px; padding:10px 22px;
        box-shadow:0 0 20px rgba(0,240,255,0.4); }
    section[data-testid="stSidebar"] { background:rgba(5,1,15,0.95); border-right:1px solid rgba(255,43,214,0.3); }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color:#ff2bd6 !important;
        text-shadow:0 0 8px #ff2bd6; font-size:14px; }
    .stTabs [data-baseweb="tab-list"] { gap:6px; background:rgba(0,0,0,0.4); padding:5px; border-radius:10px; border:1px solid rgba(0,240,255,0.2); }
    .stTabs [data-baseweb="tab"] { color:#888; font-family:'Orbitron',sans-serif; font-size:12px; letter-spacing:1px; border-radius:6px; }
    .stTabs [aria-selected="true"] { background:rgba(0,240,255,0.15) !important; color:#00f0ff !important; text-shadow:0 0 6px #00f0ff; }
    .alert-buy { border-left:4px solid #39ff14; background:rgba(57,255,20,0.08); padding:10px 14px; margin:6px 0;
        border-radius:6px; box-shadow:0 0 12px rgba(57,255,20,0.2); color:#c8ffd0; }
    .alert-sell { border-left:4px solid #ff3131; background:rgba(255,49,49,0.08); padding:10px 14px; margin:6px 0;
        border-radius:6px; box-shadow:0 0 12px rgba(255,49,49,0.2); color:#ffd0d0; }
    .alert-info { border-left:4px solid #00f0ff; background:rgba(0,240,255,0.06); padding:10px 14px; margin:6px 0;
        border-radius:6px; color:#b0ecff; }
    .alert-time { color:#666; font-size:11px; }
    .panel { background:rgba(0,0,0,0.4); border:1px solid rgba(0,240,255,0.25); border-radius:10px;
        padding:16px; margin:10px 0; box-shadow:0 0 20px rgba(0,240,255,0.08); }
    .panel-title { color:#00f0ff; font-family:'Orbitron',sans-serif; letter-spacing:2px; font-size:14px;
        margin-bottom:10px; text-shadow:0 0 6px #00f0ff; }
    .footer-note { text-align:center; color:#444; font-size:11px; margin-top:30px; padding-top:14px;
        border-top:1px solid rgba(0,240,255,0.15); }
    </style>
    """,
    unsafe_allow_html=True,
)

if "cash" not in st.session_state:
    init_wallet()

# ---------------- NOTIFICATIONS ----------------
def push_alert(alert_type, text):
    now = datetime.now().strftime("%H:%M:%S")
    st.session_state.alerts.insert(0, {"time": now, "type": alert_type, "text": text})
    if len(st.session_state.alerts) > 30:
        st.session_state.alerts = st.session_state.alerts[:30]
    icon = "🟢" if alert_type == "buy" else ("🔴" if alert_type == "sell" else "🔵")
    st.toast(f"{icon} {text}", icon=icon)
    phone = st.session_state.get("wa_phone", "")
    apikey = st.session_state.get("wa_key", "")
    if phone and apikey:
        try:
            msg = urllib.parse.quote(f"[NEON TRADER] {text}")
            requests.get(f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={msg}&apikey={apikey}", timeout=8)
        except Exception:
            pass
    save_wallet()

# ---------------- DATA ----------------
@st.cache_data(ttl=20)
def fetch_klines(symbol, interval="15m", limit=100):
    try:
        r = requests.get(BINANCE_KLINES, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=10)
        r.raise_for_status()
        df = pd.DataFrame(r.json(), columns=["ot","open","high","low","close","volume","ct","qav","trades","tbbav","tbqav","ig"])
        for c in ["open","high","low","close","volume"]:
            df[c] = df[c].astype(float)
        return df
    except Exception:
        return None

def fetch_price(symbol):
    try:
        r = requests.get(BINANCE_PRICE, params={"symbol": symbol}, timeout=8)
        p = float(r.json()["price"])
        st.session_state.last_prices[symbol] = p
        return p
    except Exception:
        return st.session_state.last_prices.get(symbol)

# ---------------- INDICATORS ----------------
def ema(s, span): return s.ewm(span=span, adjust=False).mean()
def rsi(s, period=14):
    d = s.diff(); g = d.clip(lower=0).rolling(period).mean(); l = (-d.clip(upper=0)).rolling(period).mean()
    return 100 - (100 / (1 + (g / l.replace(0, np.nan))))
def macd(s):
    m = ema(s, 12) - ema(s, 26); sig = ema(m, 9); return m, sig, m - sig
def bollinger(s, period=20, std=2):
    mid = s.rolling(period).mean(); return mid + std*s.rolling(period).std(), mid, mid - std*s.rolling(period).std()

def analyse_coin(symbol, strategy):
    df = fetch_klines(symbol)
    if df is None or len(df) < 30:
        return {"signal": "HOLD", "price": st.session_state.last_prices.get(symbol),
                "rsi": 50.0, "score": 0, "reasons": [], "bull": 0, "bear": 0}
    close = df["close"]; price = float(close.iloc[-1]); st.session_state.last_prices[symbol] = price
    rv = float(rsi(close).iloc[-1]) if not np.isnan(rsi(close).iloc[-1]) else 50.0
    ef, es = ema(close, 12).iloc[-1], ema(close, 26).iloc[-1]
    _, _, hist = macd(close); hist_now, hist_prev = hist.iloc[-1], hist.iloc[-2]
    up, mid, lo = bollinger(close)
    vol, vol_avg = df["volume"].iloc[-1], df["volume"].iloc[-20:].mean()
    vol_spike = vol > 2 * vol_avg
    bull, bear, reasons = 0, 0, []
    if ef > es: bull += 1; reasons.append("EMA bullish")
    else: bear += 1; reasons.append("EMA bearish")
    if rv < 30: bull += 1; reasons.append("RSI oversold")
    elif rv > 70: bear += 1; reasons.append("RSI overbought")
    if hist_now > 0 and hist_now > hist_prev: bull += 1; reasons.append("MACD rising")
    elif hist_now < 0 and hist_now < hist_prev: bear += 1; reasons.append("MACD falling")
    if price <= lo.iloc[-1]: bull += 1; reasons.append("At lower BB")
    elif price >= up.iloc[-1]: bear += 1; reasons.append("At upper BB")
    if vol_spike:
        if ef > es: bull += 1; reasons.append("Vol spike up")
        else: bear += 1; reasons.append("Vol spike down")
    score = bull - bear
    if strategy == "EMA Crossover":
        signal = "BUY" if ef > es and rv < 70 else ("SELL" if ef < es else "HOLD")
    elif strategy == "RSI Mean Reversion":
        signal = "BUY" if rv < 30 else ("SELL" if rv > 70 else "HOLD")
    elif strategy == "MACD Momentum":
        signal = "BUY" if hist_now > 0 and hist_now > hist_prev else ("SELL" if hist_now < 0 and hist_now < hist_prev else "HOLD")
    elif strategy == "Bollinger Breakout":
        signal = "BUY" if price <= lo.iloc[-1] else ("SELL" if price >= up.iloc[-1] else "HOLD")
    else:
        signal = "BUY" if score >= 2 else ("SELL" if score <= -2 else "HOLD")
    return {"signal": signal, "price": price, "rsi": rv, "score": score,
            "reasons": reasons, "bull": bull, "bear": bear}

# ---------------- ENGINE ----------------
def run_engine(selected_coins, strategy):
    cash = st.session_state.cash
    positions = st.session_state.positions
    for coin in selected_coins:
        a = analyse_coin(coin, strategy); price, signal = a["price"], a["signal"]
        if price is None: continue
        if coin in positions:
            pos = positions[coin]; pnl_pct = (price - pos["avg_price"]) / pos["avg_price"]
            exit_reason = None
            if signal == "SELL": exit_reason = f"{strategy} signal"
            elif pnl_pct <= -STOP_LOSS_PCT: exit_reason = "STOP-LOSS"
            elif pnl_pct >= TAKE_PROFIT_PCT: exit_reason = "TAKE-PROFIT"
            if exit_reason:
                proceeds = pos["amount"] * price * (1 - FEE)
                pnl_gbp = proceeds - (pos["amount"] * pos["avg_price"])
                st.session_state.trades.insert(0, {"time": datetime.now().strftime("%H:%M:%S"),
                    "coin": coin, "side": "SELL", "price": round(price,4), "value": round(proceeds,2),
                    "pnl_gbp": round(pnl_gbp,2), "pnl_pct": round(pnl_pct*100,2), "reason": exit_reason})
                cash += proceeds; del positions[coin]
                push_alert("sell", f"EXIT {coin.replace('USDT','')} @ {price:.4f} | {exit_reason} | P&L GBP {pnl_gbp:+.2f} ({pnl_pct*100:+.1f}%)")
                continue
        if signal == "BUY" and coin not in positions and len(positions) < MAX_POSITIONS and cash > 10:
            spend = cash * RISK_PER_TRADE; amount = (spend * (1 - FEE)) / price
            positions[coin] = {"amount": amount, "avg_price": price}; cash -= spend
            reason_str = ", ".join(a["reasons"][:3])
            st.session_state.trades.insert(0, {"time": datetime.now().strftime("%H:%M:%S"),
                "coin": coin, "side": "BUY", "price": round(price,4), "value": round(spend,2),
                "pnl_gbp": 0.0, "pnl_pct": 0.0, "reason": reason_str})
            push_alert("buy", f"BUY {coin.replace('USDT','')} @ {price:.4f} | GBP {spend:.2f} | Setup: {reason_str}")
    st.session_state.cash = cash
    holdings = sum(pos["amount"] * st.session_state.last_prices.get(c, pos["avg_price"]) for c, pos in positions.items())
    total = cash + holdings
    st.session_state.equity.append((datetime.now().strftime("%H:%M:%S"), round(total, 2)))
    if len(st.session_state.equity) > 500: st.session_state.equity = st.session_state.equity[-500:]
    save_wallet()
    return total, holdings

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## AGENT CONTROL")
    selected_coins = st.multiselect("Coins", ALL_COINS, default=["BTCUSDT","ETHUSDT","SOLUSDT"])
    strategy = st.selectbox("Strategy", STRATEGIES, index=0)
    auto = st.checkbox("Auto-trade (30s loop)", value=True)
    st.divider()
    st.markdown("## WHATSAPP ALERTS")
    st.caption("Message +34 644 50 32 43 'I allow callmebot to send me messages' to get your API key.")
    wa_phone = st.text_input("Phone (e.g. 447700900123)", key="wa_phone")
    wa_key = st.text_input("CallMeBot API key", key="wa_key")
    if st.button("Send test WhatsApp"):
        if wa_phone and wa_key:
            push_alert("info", "Test alert from NEON TRADER - working!")
            st.success("Test sent.")
        else:
            st.warning("Enter phone and API key first.")
    st.divider()
    if st.button("RESET WALLET GBP 1000"):
        if os.path.exists(WALLET_FILE): os.remove(WALLET_FILE)
        init_wallet(); st.rerun()

try:
    from streamlit_autorefresh import st_autorefresh
    if auto: st_autorefresh(interval=REFRESH_SECONDS * 1000, key="neon_refresh")
except Exception:
    st.caption("streamlit-autorefresh recommended (in requirements).")

# ---------------- HEADER ----------------
st.markdown(f"""
    <div class="neon-header">
        <h1>⚡ NEON TRADER ⚡</h1>
        <div class="sub">GBP 1000 BANK &middot; {strategy.upper()} &middot; LIVE 24/7</div>
        <div class="status-chip">{'AGENT ONLINE - SCANNING' if auto else 'PAUSED'}</div>
    </div>""", unsafe_allow_html=True)

total, holdings = run_engine(selected_coins, strategy)
pnl = total - DEFAULT_BANK; pnl_pct = pnl / DEFAULT_BANK * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("PORTFOLIO", f"GBP {total:.2f}")
c2.metric("CASH", f"GBP {st.session_state.cash:.2f}")
c3.metric("P&L", f"GBP {pnl:+.2f}", f"{pnl_pct:+.1f}%")
c4.metric("OPEN TRADES", len(st.session_state.positions))

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="panel"><div class="panel-title">▓▒░ LIVE ACTIVITY - WHAT THE AGENT IS DOING</div>', unsafe_allow_html=True)
for al in st.session_state.alerts[:10]:
    cls = "alert-buy" if al["type"] == "buy" else ("alert-sell" if al["type"] == "sell" else "alert-info")
    st.markdown(f'<div class="{cls}"><span class="alert-time">[{al["time"]}]</span> {al["text"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

tab_sig, tab_pos, tab_log, tab_chart = st.tabs(["SIGNALS","OPEN POSITIONS","TRADE LOG","EQUITY CURVE"])
with tab_sig:
    st.markdown('<div class="panel"><div class="panel-title">▓▒░ MARKET SIGNALS</div>', unsafe_allow_html=True)
    rows = []
    for coin in selected_coins:
        a = analyse_coin(coin, strategy)
        rows.append({"coin": coin.replace("USDT",""), "price": round(a["price"],4) if a["price"] else "-",
                     "RSI": round(a["rsi"],1), "bull/bear": f"{a.get('bull',0)}/{a.get('bear',0)}",
                     "confluence": a.get("score",0), "signal": a["signal"],
                     "setup": ", ".join(a.get("reasons",[])[:3])})
    df_sig = pd.DataFrame(rows)
    def color_sig(row):
        c = "rgba(57,255,20,0.15)" if row["signal"]=="BUY" else ("rgba(255,49,49,0.15)" if row["signal"]=="SELL" else "")
        return [f"background-color:{c}"]*len(row)
    st.dataframe(df_sig.style.apply(color_sig, axis=1), use_container_width=True)
    st.caption("BUY=green SELL=red HOLD=none. Confluence = bullish minus bearish setups.")
    st.markdown('</div>', unsafe_allow_html=True)
with tab_pos:
    if not st.session_state.positions:
        st.info("No open positions. Agent buys on good setups only.")
    else:
        rows = []
        for coin, pos in st.session_state.positions.items():
            p = st.session_state.last_prices.get(coin, pos["avg_price"])
            pnl_p = (p - pos["avg_price"])/pos["avg_price"]*100
            rows.append({"coin": coin.replace("USDT",""), "amount": round(pos["amount"],6),
                         "entry": round(pos["avg_price"],4), "now": round(p,4),
                         "value GBP": round(pos["amount"]*p,2), "pnl %": round(pnl_p,2)})
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
with tab_log:
    if not st.session_state.trades: st.info("No trades yet.")
    else: st.dataframe(pd.DataFrame(st.session_state.trades), use_container_width=True)
with tab_chart:
    if len(st.session_state.equity) > 1:
        import plotly.graph_objects as go
        eq = pd.DataFrame(st.session_state.equity, columns=["time","value"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=eq["time"], y=eq["value"], mode="lines", line=dict(color="#00f0ff",width=2),
                                 fill="tozeroy", fillcolor="rgba(0,240,255,0.1)"))
        fig.add_hline(y=DEFAULT_BANK, line_dash="dash", line_color="#ff2bd6", annotation_text="Start GBP 1000")
        fig.update_layout(height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#00f0ff", family="Share Tech Mono"), margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("Equity curve building - wait for next refresh.")

st.markdown('<div class="footer-note">NEON TRADER v2 &middot; GBP 1000 paper bank &middot; Persistent wallet &middot; Not financial advice &middot; Crypto unregulated - risk total loss &middot; 18+</div>', unsafe_allow_html=True)
