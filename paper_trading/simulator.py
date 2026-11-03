import pandas as pd

from strategies.signal import generate_signal


# =====================================
# PAPER TRADING CONFIGURATION
# =====================================

INITIAL_BALANCE = 5000.0

LEVERAGE = 2

RISK_PERCENT = 0.005

STOP_LOSS_PERCENT = 0.01

TAKE_PROFIT_PERCENT = 0.02

TRADING_FEE = 0.0005


# =====================================
# SIMULATION ENGINE
# =====================================

def run_simulation(df, ema_fast=9, ema_slow=21):

    balance = INITIAL_BALANCE
    position = None

    trades = []

    equity_history = [balance]

    # Mulai setelah tersedia minimal 50 candle
    for i in range(50, len(df)):

        candle = df.iloc[i]

        # =================================
        # 1. CEK POSISI YANG SEDANG TERBUKA
        # =================================

        if position is not None:

            side = position["side"]

            entry = position["entry"]
            quantity = position["quantity"]

            stop_loss = position["stop_loss"]
            take_profit = position["take_profit"]

            exit_price = None
            exit_reason = None

            if side == "LONG":

                sl_hit = candle["low"] <= stop_loss
                tp_hit = candle["high"] >= take_profit

            else:

                sl_hit = candle["high"] >= stop_loss
                tp_hit = candle["low"] <= take_profit

            # Jika SL dan TP tersentuh pada candle yang sama,
            # gunakan asumsi konservatif: SL terjadi lebih dahulu.

            if sl_hit:
                exit_price = stop_loss
                exit_reason = "STOP LOSS"

            elif tp_hit:
                exit_price = take_profit
                exit_reason = "TAKE PROFIT"

            if exit_price is not None:

                direction = (
                    1 if side == "LONG" else -1
                )

                gross_pnl = (
                    direction
                    * (exit_price - entry)
                    * quantity
                )

                exit_fee = (
                    quantity
                    * exit_price
                    * TRADING_FEE
                )

                entry_fee = position["entry_fee"]

                net_pnl = (
                    gross_pnl
                    - entry_fee
                    - exit_fee
                )

                balance += net_pnl

                trades.append({
                    "side": side,
                    "entry_time": position["entry_time"],
                    "exit_time": candle["open_time"],
                    "entry_price": entry,
                    "exit_price": exit_price,
                    "quantity": quantity,
                    "gross_pnl": gross_pnl,
                    "entry_fee": entry_fee,
                    "exit_fee": exit_fee,
                    "net_pnl": net_pnl,
                    "exit_reason": exit_reason,
                    "balance": balance
                })

                equity_history.append(balance)

                position = None

                # Tidak membuka posisi baru pada candle exit
                continue

        # =================================
        # 2. JIKA TIDAK ADA POSISI
        # =================================

        if position is None:

            # Gunakan data sampai candle sebelumnya saja.
            # Candle saat ini merupakan candle eksekusi.
            historical_data = df.iloc[:i]

            signal = generate_signal(
                historical_data
            )

            if signal["signal"] not in [
                "LONG",
                "SHORT"
            ]:
                continue

            # Entry pada OPEN candle berikutnya
            entry_price = float(candle["open"])

            # Besar risiko berdasarkan equity
            risk_amount = balance * RISK_PERCENT

            # Hitung notional berdasarkan jarak SL
            notional = (
                risk_amount / STOP_LOSS_PERCENT
            )

            # Batasi notional sesuai leverage
            max_notional = balance * LEVERAGE

            notional = min(
                notional,
                max_notional
            )

            quantity = notional / entry_price

            entry_fee = notional * TRADING_FEE

            # Jangan membuka posisi jika saldo tidak cukup
            if notional / LEVERAGE + entry_fee > balance:
                continue

            if signal["signal"] == "LONG":

                side = "LONG"

                stop_loss = (
                    entry_price
                    * (1 - STOP_LOSS_PERCENT)
                )

                take_profit = (
                    entry_price
                    * (1 + TAKE_PROFIT_PERCENT)
                )

            else:

                side = "SHORT"

                stop_loss = (
                    entry_price
                    * (1 + STOP_LOSS_PERCENT)
                )

                take_profit = (
                    entry_price
                    * (1 - TAKE_PROFIT_PERCENT)
                )

            position = {
                "side": side,
                "entry": entry_price,
                "entry_time": candle["open_time"],
                "quantity": quantity,
                "notional": notional,
                "entry_fee": entry_fee,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }

    # =================================
    # 3. TUTUP POSISI DI AKHIR DATA
    # =================================

    if position is not None:

        last_candle = df.iloc[-1]

        exit_price = float(last_candle["close"])

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

        net_pnl = (
            gross_pnl
            - position["entry_fee"]
            - exit_fee
        )

        balance += net_pnl

        trades.append({
            "side": position["side"],
            "entry_time": position["entry_time"],
            "exit_time": last_candle["open_time"],
            "entry_price": position["entry"],
            "exit_price": exit_price,
            "quantity": position["quantity"],
            "gross_pnl": gross_pnl,
            "entry_fee": position["entry_fee"],
            "exit_fee": exit_fee,
            "net_pnl": net_pnl,
            "exit_reason": "END OF DATA",
            "balance": balance
        })

        equity_history.append(balance)

    return {
        "initial_balance": INITIAL_BALANCE,
        "final_balance": balance,
        "trades": trades,
        "equity_history": equity_history
    }


# =====================================
# PERFORMANCE STATISTICS
# =====================================

def calculate_statistics(result):

    trades = result["trades"]

    if not trades:

        return {
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "total_profit": 0,
            "total_loss": 0,
            "net_profit": 0,
            "max_drawdown": 0
        }

    df = pd.DataFrame(trades)

    winners = df[df["net_pnl"] > 0]
    losers = df[df["net_pnl"] < 0]

    total_profit = winners["net_pnl"].sum()

    total_loss = abs(
        losers["net_pnl"].sum()
    )

    total_trades = len(df)

    win_rate = (
        len(winners) / total_trades
    ) * 100

    if total_loss > 0:
        profit_factor = total_profit / total_loss
    elif total_profit > 0:
        profit_factor = float("inf")
    else:
        profit_factor = 0

    equity = pd.Series(
        result["equity_history"],
        dtype=float
    )

    peak = equity.cummax()

    drawdown = (
        (peak - equity) / peak
    ) * 100

    max_drawdown = drawdown.max()

    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "total_profit": total_profit,
        "total_loss": total_loss,
        "net_profit": df["net_pnl"].sum(),
        "max_drawdown": max_drawdown
    }