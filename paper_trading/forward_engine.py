
import pandas as pd

from strategies.signal import generate_signal

from paper_trading.database import (
    initialize_session,
    load_state,
    save_candle_result
)


# =====================================
# CONFIGURATION
# =====================================

INITIAL_BALANCE = 5000.0

LEVERAGE = 2

RISK_PERCENT = 0.005

STOP_LOSS_PERCENT = 0.01

TAKE_PROFIT_PERCENT = 0.02

TRADING_FEE = 0.0005


# =====================================
# CHECK EXIT CONDITIONS
# =====================================

def check_exit(position, candle):

    side = position["side"]

    sl = position["stop_loss"]
    tp = position["take_profit"]

    if side == "LONG":

        sl_hit = candle["low"] <= sl
        tp_hit = candle["high"] >= tp

    else:

        sl_hit = candle["high"] >= sl
        tp_hit = candle["low"] <= tp

    # Conservative assumption:
    # If SL and TP are both touched, SL first.

    if sl_hit:

        return sl, "STOP LOSS"

    if tp_hit:

        return tp, "TAKE PROFIT"

    return None, None


# =====================================
# OPEN POSITION
# =====================================

def open_position(signal, candle, balance):

    side = signal["signal"]

    entry = float(candle["open"])

    risk_amount = balance * RISK_PERCENT

    notional = risk_amount / STOP_LOSS_PERCENT

    max_notional = balance * LEVERAGE

    notional = min(notional, max_notional)

    quantity = notional / entry

    entry_fee = notional * TRADING_FEE

    required_margin = notional / LEVERAGE

    if required_margin + entry_fee > balance:

        return None, balance

    if side == "LONG":

        stop_loss = (
            entry * (1 - STOP_LOSS_PERCENT)
        )

        take_profit = (
            entry * (1 + TAKE_PROFIT_PERCENT)
        )

    else:

        stop_loss = (
            entry * (1 + STOP_LOSS_PERCENT)
        )

        take_profit = (
            entry * (1 - TAKE_PROFIT_PERCENT)
        )

    position = {

        "side": side,

        "entry": entry,

        "entry_time": str(candle["open_time"]),

        "quantity": quantity,

        "notional": notional,

        "entry_fee": entry_fee,

        "stop_loss": stop_loss,

        "take_profit": take_profit

    }

    # Deduct entry fee immediately
    balance -= entry_fee

    return position, balance


# =====================================
# CLOSE POSITION
# =====================================

def close_position(
    position,
    exit_price,
    exit_time,
    reason,
    balance
):

    direction = (
        1 if position["side"] == "LONG" else -1
    )

    gross_pnl = (
        direction
        * (exit_price - position["entry"])
        * position["quantity"]
    )

    exit_fee = (
        position["quantity"]
        * exit_price
        * TRADING_FEE
    )

    entry_fee = position["entry_fee"]

    net_pnl = (
        gross_pnl
        - entry_fee
        - exit_fee
    )

    # Entry fee was already deducted
    balance += gross_pnl - exit_fee

    trade = {

        "side": position["side"],

        "entry_time": position["entry_time"],

        "exit_time": str(exit_time),

        "entry_price": position["entry"],

        "exit_price": exit_price,

        "quantity": position["quantity"],

        "gross_pnl": gross_pnl,

        "entry_fee": entry_fee,

        "exit_fee": exit_fee,

        "net_pnl": net_pnl,

        "exit_reason": reason,

        "balance": balance

    }

    return balance, trade


# =====================================
# FORWARD PAPER TRADING ENGINE
# =====================================

def process_new_candles(df, ema_fast=9, ema_slow=21):

    if len(df) < 51:

        return {
            "status": "WAITING_FOR_DATA",
            "new_trades": [],
            "processed": 0
        }

    df = df.copy().reset_index(drop=True)

    latest_time = str(df.iloc[-1]["open_time"])

    # First launch:
    # Initialize the session at the latest candle.
    # Do not simulate old candles as forward trades.

    is_new_session = initialize_session(
        latest_time
    )

    if is_new_session:

        return {
            "status": "SESSION_INITIALIZED",
            "new_trades": [],
            "processed": 0
        }

    state = load_state()

    balance = float(state["balance"])

    position = state["position"]

    last_time = pd.to_datetime(
        state["last_processed_open_time"],
        utc=True
    )

    new_trades = []

    processed = 0

    # Process only candles not previously processed
    for i in range(len(df)):

        candle = df.iloc[i]

        candle_time = pd.to_datetime(
            candle["open_time"],
            utc=True
        )

        if candle_time <= last_time:
            continue

        # We need at least 50 previous candles
        if i < 50:

            save_candle_result(
                balance,
                position,
                candle["open_time"]
            )

            last_time = candle_time
            processed += 1

            continue

        trade = None

        # =================================
        # EXISTING POSITION
        # =================================

        if position is not None:

            exit_price, reason = check_exit(
                position,
                candle
            )

            if exit_price is not None:

                balance, trade = close_position(
                    position,
                    exit_price,
                    candle["open_time"],
                    reason,
                    balance
                )

                new_trades.append(trade)

                position = None

            # Do not open another position
            # on the same candle after an exit.

        # =================================
        # NO EXISTING POSITION
        # =================================

        else:

            # Signal is calculated using previous candles only.
            previous_candles = df.iloc[:i]

            signal = generate_signal(
                previous_candles,
                ema_fast=ema_fast,
                ema_slow=ema_slow
            )

            if signal["signal"] in ["LONG", "SHORT"]:

                position, balance = open_position(
                    signal,
                    candle,
                    balance
                )

                # Evaluate SL/TP on entry candle.
                if position is not None:

                    exit_price, reason = check_exit(
                        position,
                        candle
                    )

                    if exit_price is not None:

                        balance, trade = close_position(
                            position,
                            exit_price,
                            candle["open_time"],
                            reason,
                            balance
                        )

                        new_trades.append(trade)

                        position = None

        # =================================
        # SAVE PROCESSED CANDLE
        # =================================

        save_candle_result(
            balance,
            position,
            candle["open_time"],
            trade
        )

        last_time = candle_time

        processed += 1

    return {

        "status": "RUNNING",

        "new_trades": new_trades,

        "processed": processed

    }
