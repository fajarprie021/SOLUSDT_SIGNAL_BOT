import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

from data.binance_data import get_market_data
from indicators.technical import calculate_indicators
from strategies.signal import generate_signal

from paper_trading.optimizer import optimize_ema
from paper_trading.simulator import (
    run_simulation,
    calculate_statistics
)

from paper_trading.forward_engine import (
    process_new_candles
)

from paper_trading.database import (
    load_state,
    get_trade_history,
    reset_session
)

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="SOLUSDT Agent Desk",
    page_icon="📈",
    layout="wide"
)

# ==========================================
# CUSTOM STYLE
# ==========================================

st.markdown("""
<style>
    .stApp {
        background-color: #0b1120;
        color: #ffffff;
    }

    [data-testid="stMetric"] {
        background-color: #151e30;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #273449;
    }

    h1, h2, h3 {
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

@st.cache_data(ttl=30)
def load_market_data(symbol, timeframe, limit, ema_fast=9, ema_slow=21):
    df = get_market_data(
        symbol=symbol,
        interval=timeframe,
        limit=limit
    )
    df = calculate_indicators(
        df,
        ema_fast=ema_fast,
        ema_slow=ema_slow,
        rsi_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9
    )
    return df

def calculate_forward_stats(trades, initial_balance=5000.0):

    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_profit": 0.0,
            "total_loss": 0.0,
            "net_profit": 0.0,
            "max_drawdown": 0.0,
            "equity_curve": [initial_balance]
        }

    df = pd.DataFrame(trades)

    if "id" in df.columns:
        df = df.sort_values("id")
    else:
        df = df.iloc[::-1].reset_index(drop=True)

    winners = df[df["net_pnl"] > 0]
    losers = df[df["net_pnl"] < 0]

    total_profit = winners["net_pnl"].sum()
    total_loss = abs(losers["net_pnl"].sum())

    total_trades = len(df)
    win_rate = (len(winners) / total_trades) * 100 if total_trades > 0 else 0

    if total_loss > 0:
        profit_factor = total_profit / total_loss
    elif total_profit > 0:
        profit_factor = float("inf")
    else:
        profit_factor = 0.0

    net_profit = df["net_pnl"].sum()

    equity_curve = [initial_balance] + df["balance"].tolist()
    equity_series = pd.Series(equity_curve, dtype=float)
    peak = equity_series.cummax()
    drawdown = ((peak - equity_series) / peak) * 100
    max_drawdown = drawdown.max()

    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "total_profit": total_profit,
        "total_loss": total_loss,
        "net_profit": net_profit,
        "max_drawdown": max_drawdown,
        "equity_curve": equity_curve
    }

# ==========================================
# HEADER
# ==========================================

st.title("SOLUSDT AGENT DESK")
st.caption("BINANCE FUTURES | EMA + RSI + MACD | FORWARD PAPER TRADING + HISTORICAL ANALYSIS")
st.divider()

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("BOT CONFIGURATION")

symbol = st.sidebar.selectbox(
    "Trading Pair",
    ["SOLUSDT"]
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1m"]
)

limit = st.sidebar.selectbox(
    "Historical Candles",
    [500, 1000],
    index=1
)

auto_refresh = st.sidebar.checkbox(
    "Auto Refresh",
    value=True
)

refresh_seconds = st.sidebar.selectbox(
    "Refresh Interval (seconds)",
    [10, 15, 30, 60],
    index=1
)

refresh_now = st.sidebar.button(
    "REFRESH NOW",
    use_container_width=True
)

if st.sidebar.button(
    "RESET FORWARD SESSION",
    use_container_width=True
):
    reset_session()
    st.cache_data.clear()
    st.sidebar.success("Forward session berhasil di-reset.")
    st.rerun()

st.sidebar.info(
    "Mode: FORWARD PAPER TRADING\n\n"
    "Real Order: DISABLED\n\n"
    "Database: SQLite\n\n"
    "Initial Forward Balance: 5,000 USDT"
)

st.sidebar.divider()

st.sidebar.subheader("EMA STRATEGY SETTINGS")

if "ema_fast_input" not in st.session_state:
    st.session_state["ema_fast_input"] = 9
if "ema_slow_input" not in st.session_state:
    st.session_state["ema_slow_input"] = 21

ema_fast = st.sidebar.number_input(
    "EMA Fast",
    min_value=2,
    max_value=50,
    step=1,
    key="ema_fast_input"
)

ema_slow = st.sidebar.number_input(
    "EMA Slow",
    min_value=3,
    max_value=200,
    step=1,
    key="ema_slow_input"
)

if ema_fast >= ema_slow:
    st.sidebar.error(
        "EMA Fast harus lebih kecil dari EMA Slow."
    )
    st.stop()
# ==========================================
# AUTO REFRESH
# ==========================================

if auto_refresh:
    st_autorefresh(
        interval=refresh_seconds * 1000,
        key="solusdt_auto_refresh"
    )

if refresh_now:
    st.cache_data.clear()

# ==========================================
# MARKET DATA
# ==========================================

try:

    with st.spinner("Loading Binance Futures data..."):

        df = load_market_data(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            ema_fast=ema_fast,
            ema_slow=ema_slow
        )

    if len(df) < 100:

        st.error("Market data tidak mencukupi.")
        st.stop()

except Exception as e:

    st.error(f"Market connection error: {e}")
    st.stop()
# ==========================================
# PROCESS FORWARD ENGINE
# ==========================================

try:
    forward_result = process_new_candles(
        df,
        ema_fast=ema_fast,
        ema_slow=ema_slow
    )
except Exception as e:
    st.error(f"Forward engine error: {e}")
    forward_result = {
        "status": "ERROR",
        "processed": 0,
        "new_trades": []
    }
forward_state = load_state()
forward_trades = get_trade_history()
forward_stats = calculate_forward_stats(
    forward_trades,
    initial_balance=5000.0
)

# ==========================================
# HISTORICAL SIMULATION
# ==========================================

try:
    historical_result = run_simulation(
        df,
        ema_fast=ema_fast,
        ema_slow=ema_slow
    )
    historical_stats = calculate_statistics(historical_result)
except Exception as e:
    st.error(f"Historical simulation error: {e}")
    historical_result = None
    historical_stats = None

# ==========================================
# CURRENT MARKET + SIGNAL
# ==========================================

latest = df.iloc[-1]
try:
    signal = generate_signal(df, ema_fast=ema_fast, ema_slow=ema_slow)
except Exception as e:
    st.error(f"Signal calculation error: {e}")
    signal = {
        "signal": "WAIT",
        "reason": "Signal engine belum kompatibel dengan parameter EMA."
    }

price = float(latest["close"])

# ==========================================
# TOP LIVE METRICS
# ==========================================

st.subheader("LIVE MARKET OVERVIEW")

m1, m2, m3, m4 = st.columns(4)

m1.metric("SOLUSDT PRICE", f"{price:.4f} USDT")
m2.metric(
    f"EMA {ema_fast}",
    f"{latest['ema_fast'] if 'ema_fast' in latest.index else latest['ema_9']:.5f}"
)
m3.metric(
    f"EMA {ema_slow}",
    f"{latest['ema_slow'] if 'ema_slow' in latest.index else latest['ema_21']:.5f}"
)
m4.metric("RSI 14", f"{latest['rsi']:.2f}")

st.divider()

# ==========================================
# FORWARD STATUS PANEL
# ==========================================

st.subheader("FORWARD ENGINE STATUS")

s1, s2, s3, s4 = st.columns(4)

s1.metric("ENGINE STATUS", forward_result["status"])
s2.metric("NEW CANDLES", forward_result["processed"])
s3.metric("NEW TRADES", len(forward_result["new_trades"]))
s4.metric("LAST CANDLE", str(latest["open_time"]))

# ==========================================
# SIGNAL PANEL
# ==========================================

st.divider()
st.subheader("CURRENT SIGNAL")

sig1, sig2 = st.columns(2)

with sig1:
    current_signal = signal["signal"]

    if current_signal == "LONG":
        st.success("LONG SIGNAL")
    elif current_signal == "SHORT":
        st.error("SHORT SIGNAL")
    else:
        st.warning("WAIT SIGNAL")

    st.write(signal["reason"])

with sig2:
    st.metric("MACD", f"{latest['macd']:.6f}")
    st.metric("MACD SIGNAL", f"{latest['macd_signal']:.6f}")
    st.metric("MACD HISTOGRAM", f"{latest['macd_hist']:.6f}")

# ==========================================
# FORWARD SESSION METRICS
# ==========================================

st.divider()
st.subheader("FORWARD PAPER TRADING SESSION")

forward_balance = 5000.0
open_position = None
session_started_at = "-"

if forward_state is not None:
    forward_balance = float(forward_state["balance"])
    open_position = forward_state["position"]
    session_started_at = forward_state["session_started_at"]

f1, f2, f3, f4 = st.columns(4)

f1.metric("Current Balance", f"{forward_balance:,.2f} USDT")
f2.metric("Net Profit", f"{forward_stats['net_profit']:.2f} USDT")
f3.metric("Total Trades", forward_stats["total_trades"])
f4.metric("Win Rate", f"{forward_stats['win_rate']:.2f}%")

f5, f6, f7 = st.columns(3)

f5.metric(
    "Profit Factor",
    f"{forward_stats['profit_factor']:.2f}"
    if forward_stats["profit_factor"] != float("inf")
    else "∞"
)

f6.metric("Total Loss", f"{forward_stats['total_loss']:.2f} USDT")
f7.metric("Max Drawdown", f"{forward_stats['max_drawdown']:.2f}%")

st.caption(f"Forward session started at: {session_started_at}")

# ==========================================
# OPEN POSITION PANEL
# ==========================================

st.divider()
st.subheader("OPEN POSITION")

if open_position is not None:

    p1, p2, p3, p4, p5 = st.columns(5)

    p1.metric("SIDE", open_position["side"])
    p2.metric("ENTRY", f"{float(open_position['entry']):.4f}")
    p3.metric("STOP LOSS", f"{float(open_position['stop_loss']):.4f}")
    p4.metric("TAKE PROFIT", f"{float(open_position['take_profit']):.4f}")
    p5.metric("QUANTITY", f"{float(open_position['quantity']):.6f}")

else:
    st.info("Saat ini tidak ada posisi forward yang terbuka.")

# ==========================================
# PRICE CHART
# ==========================================

st.divider()
st.subheader("PRICE CHART")

fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.06,
    row_heights=[0.60, 0.20, 0.20],
    subplot_titles=(
        "SOLUSDT Candlestick + EMA",
        "RSI 14",
        "MACD"
    )
)

fig.add_trace(
    go.Candlestick(
        x=df["open_time"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="SOLUSDT"
    ),
    row=1,
    col=1
)

fig.add_trace(
    go.Scatter(
        x=df["open_time"],
        y=df["ema_fast"] if "ema_fast" in df.columns else df["ema_9"],
        name=f"EMA {ema_fast}"
    ),
    row=1,
    col=1
)

fig.add_trace(
    go.Scatter(
        x=df["open_time"],
        y=df["ema_slow"] if "ema_slow" in df.columns else df["ema_21"],
        name=f"EMA {ema_slow}"
    ),
    row=1,
    col=1
)

fig.add_trace(
    go.Scatter(
        x=df["open_time"],
        y=df["rsi"],
        name="RSI 14"
    ),
    row=2,
    col=1
)

fig.add_hline(y=70, line_dash="dash", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", row=2, col=1)

fig.add_trace(
    go.Scatter(
        x=df["open_time"],
        y=df["macd"],
        name="MACD"
    ),
    row=3,
    col=1
)

fig.add_trace(
    go.Scatter(
        x=df["open_time"],
        y=df["macd_signal"],
        name="MACD Signal"
    ),
    row=3,
    col=1
)

fig.add_trace(
    go.Bar(
        x=df["open_time"],
        y=df["macd_hist"],
        name="MACD Histogram"
    ),
    row=3,
    col=1
)

fig.update_layout(
    height=850,
    template="plotly_dark",
    xaxis_rangeslider_visible=False,
    legend_orientation="h",
    margin=dict(l=20, r=20, t=50, b=20)
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# EQUITY CURVE FORWARD
# ==========================================

st.divider()
st.subheader("FORWARD EQUITY CURVE")

forward_equity_fig = go.Figure()

forward_equity_fig.add_trace(
    go.Scatter(
        y=forward_stats["equity_curve"],
        mode="lines+markers",
        name="Forward Equity"
    )
)

forward_equity_fig.update_layout(
    template="plotly_dark",
    height=350,
    xaxis_title="Closed Trades",
    yaxis_title="Balance (USDT)"
)

st.plotly_chart(
    forward_equity_fig,
    use_container_width=True
)

# ==========================================
# FORWARD TRADE HISTORY
# ==========================================

st.divider()
st.subheader("FORWARD TRADE HISTORY")

if forward_trades:

    forward_trade_df = pd.DataFrame(forward_trades)

    if "id" in forward_trade_df.columns:
        forward_trade_df = forward_trade_df.sort_values(
            "id",
            ascending=False
        )

    st.dataframe(
        forward_trade_df,
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("Belum ada trade forward yang selesai.")

# ==========================================
# HISTORICAL COMPARISON
# ==========================================

st.divider()
st.subheader("HISTORICAL PAPER SIMULATION (COMPARISON ONLY)")

h1, h2, h3, h4 = st.columns(4)

if historical_result is not None and historical_stats is not None:
    h1.metric("Initial Balance", f"{historical_result['initial_balance']:,.2f} USDT")
    h2.metric("Final Balance", f"{historical_result['final_balance']:,.2f} USDT")
    h3.metric("Net Profit", f"{historical_stats['net_profit']:.2f} USDT")
    h4.metric("Total Trades", historical_stats["total_trades"])

    h5, h6, h7 = st.columns(3)
    h5.metric("Win Rate", f"{historical_stats['win_rate']:.2f}%")
    h6.metric(
        "Profit Factor",
        f"{historical_stats['profit_factor']:.2f}"
        if historical_stats["profit_factor"] != float("inf")
        else "∞"
    )
    h7.metric("Max Drawdown", f"{historical_stats['max_drawdown']:.2f}%")
else:
    st.warning("Historical metrics belum tersedia. Periksa pesan error simulasi di atas.")


# ==========================================
# MULTI-STRATEGY EMA OPTIMIZER
# ==========================================

st.divider()
st.header("MULTI-STRATEGY EMA OPTIMIZER")
st.caption(
    "Historical comparison only | SOLUSDT | 1m | RSI 14 | MACD 12/26/9"
)

opt1, opt2, opt3, opt4 = st.columns(4)

with opt1:
    fast_start = st.number_input(
        "Fast EMA Start", min_value=2, max_value=50,
        value=5, step=1, key="opt_fast_start"
    )
with opt2:
    fast_end = st.number_input(
        "Fast EMA End", min_value=2, max_value=50,
        value=20, step=1, key="opt_fast_end"
    )
with opt3:
    fast_step = st.number_input(
        "Fast EMA Step", min_value=1, max_value=20,
        value=1, step=1, key="opt_fast_step"
    )
with opt4:
    optimizer_slow = st.number_input(
        "Optimizer Slow EMA", min_value=3, max_value=200,
        value=21, step=1, key="opt_slow"
    )

fast_values = list(range(int(fast_start), int(fast_end) + 1, int(fast_step)))
valid_fast_values = [v for v in fast_values if v < int(optimizer_slow)]

st.info(
    f"Konfigurasi optimizer: Fast {fast_start}–{fast_end}, "
    f"step {fast_step}, Slow {optimizer_slow}. "
    f"Total kombinasi valid: {len(valid_fast_values)}."
)

if st.button(
    "RUN EMA OPTIMIZATION",
    type="primary",
    use_container_width=True,
    disabled=(fast_start > fast_end or len(valid_fast_values) == 0)
):
    try:
        with st.spinner(f"Menguji {len(valid_fast_values)} kombinasi EMA..."):
            optimization_result = optimize_ema(
                raw_df=df,
                fast_values=fast_values,
                slow_values=[int(optimizer_slow)]
            )
        st.session_state["ema_optimization_result"] = optimization_result
        st.success(
            f"Optimasi selesai: {len(optimization_result)} kombinasi diuji."
        )
    except Exception as e:
        st.error(
            "EMA optimizer gagal dijalankan. Pastikan simulator.py "
            "mendukung run_simulation(df, ema_fast=..., ema_slow=...). "
            f"Detail: {e}"
        )

if "ema_optimization_result" in st.session_state:
    result_df = st.session_state["ema_optimization_result"]

    if result_df is not None and not result_df.empty:
        st.subheader("OPTIMIZATION RESULTS")

        best = result_df.iloc[0]
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Top EMA Fast", int(best["EMA Fast"]))
        b2.metric("EMA Slow", int(best["EMA Slow"]))
        b3.metric("Net Profit", f"{best['Net Profit (USDT)']:.2f} USDT")
        b4.metric("Win Rate", f"{best['Win Rate (%)']:.2f}%")

        st.dataframe(result_df, use_container_width=True, hide_index=True)

        profit_fig = go.Figure()
        labels = [
            f"EMA {int(row['EMA Fast'])}/{int(row['EMA Slow'])}"
            for _, row in result_df.iterrows()
        ]
        profit_fig.add_trace(
            go.Bar(
                x=labels,
                y=result_df["Net Profit (USDT)"],
                name="Net Profit"
            )
        )
        profit_fig.update_layout(
            template="plotly_dark",
            height=380,
            xaxis_title="EMA Combination",
            yaxis_title="Net Profit (USDT)"
        )
        st.plotly_chart(profit_fig, use_container_width=True)

        st.subheader("APPLY STRATEGY TO DASHBOARD")
        strategy_labels = [
            f"EMA {int(row['EMA Fast'])}/{int(row['EMA Slow'])}"
            for _, row in result_df.iterrows()
        ]
        chosen_label = st.selectbox(
            "Pilih kombinasi EMA",
            strategy_labels,
            key="optimizer_selected_strategy"
        )
        chosen_idx = strategy_labels.index(chosen_label)
        chosen_row = result_df.iloc[chosen_idx]
        chosen_fast = int(chosen_row["EMA Fast"])
        chosen_slow = int(chosen_row["EMA Slow"])

        if open_position is not None:
            st.warning(
                "Ada posisi forward yang masih terbuka. Jangan mengganti "
                "parameter EMA sampai posisi tersebut selesai."
            )

        if st.button(
            "APPLY SELECTED EMA",
            use_container_width=True,
            disabled=(open_position is not None)
        ):
            st.session_state["ema_fast_input"] = chosen_fast
            st.session_state["ema_slow_input"] = chosen_slow
            st.rerun()
    else:
        st.info("Belum ada hasil optimasi. Klik RUN EMA OPTIMIZATION.")


# ==========================================
# FOOTER
# ==========================================

st.divider()
st.caption(
    "SOLUSDT AGENT DESK | FORWARD PAPER TRADING WITH SQLITE | "
    "REAL ORDER EXECUTION DISABLED"
)