import time
import pandas as pd

from data.binance_data import get_market_data
from data.multi_timeframe_data import (
    get_multi_timeframe_data,
    remove_incomplete_candles,
)
from strategies.trend_filter import calculate_multi_timeframe_trend
from strategies.strategy_b import generate_strategy_b_signal
from paper_trading.forward_engine_b import ForwardEngineB


# ==========================================================
# CONFIGURATION
# ==========================================================

SYMBOL = "SOLUSDT"
ENTRY_TIMEFRAME = "1m"
ENTRY_CANDLE_SECONDS = 60
ENTRY_DATA_LIMIT = 500
MTF_DATA_LIMIT = 300
POLLING_SECONDS = 5
MIN_ENTRY_CANDLES = 300

REAL_ORDERS_ENABLED = False


def prepare_entry_data(df):
    """Validate, sort, deduplicate and retain closed 1M candles."""

    if df is None or df.empty:
        raise ValueError("Data entry 1M kosong.")

    required = ["open_time", "open", "high", "low", "close", "volume"]
    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(f"Kolom data 1M tidak ditemukan: {missing}")

    data = df.copy()
    data["open_time"] = pd.to_datetime(
        data["open_time"], utc=True, errors="coerce"
    )

    for column in ["open", "high", "low", "close", "volume"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(subset=required)
    data = data.sort_values("open_time")
    data = data.drop_duplicates(subset=["open_time"], keep="last")
    data = data.reset_index(drop=True)

    data = remove_incomplete_candles(
        data,
        timeframe_seconds=ENTRY_CANDLE_SECONDS,
    )

    if len(data) < MIN_ENTRY_CANDLES:
        raise ValueError(
            f"Candle tertutup hanya {len(data)}. "
            f"Minimal {MIN_ENTRY_CANDLES} diperlukan."
        )

    return data


def candle_time_string(value):
    timestamp = pd.Timestamp(value)

    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")

    return timestamp.isoformat()


def print_account(engine, market_price):
    account = engine.get_account(price=market_price)
    position = account["open_position"]

    print("\nACCOUNT")
    print("-" * 65)
    print(f"Initial Balance : {account['initial_balance']:.2f} USDT")
    print(f"Balance         : {account['balance']:.2f} USDT")
    print(f"Available       : {account['available_balance']:.2f} USDT")
    print(f"Margin Used     : {account['margin_used']:.2f} USDT")
    print(f"Unrealized PnL  : {account['unrealized_pnl']:.4f} USDT")
    print(f"Equity          : {account['equity']:.4f} USDT")
    print(f"Leverage        : {account['leverage']}x")
    print(f"Notional        : {account['notional']:.2f} USDT")

    if position:
        print(f"Open Position   : {position['side']}")
        print(f"Entry Price     : {position['entry_price']}")
        print(f"Quantity        : {position['quantity']}")
        print(f"Stop Loss       : {position['stop_loss']}")
        print(f"Take Profit     : {position['take_profit']}")
    else:
        print("Open Position   : NONE")

    kill_status = engine.get_kill_switch_status(price=market_price)
    print(
        "Kill Switch     :",
        "ACTIVE" if kill_status["active"] else "INACTIVE",
    )
    print(
        f"Minimum Equity  : {kill_status['minimum_equity']:.2f} USDT"
    )


def print_signal(trend_result, signal_result):
    print("\nMULTI-TIMEFRAME TREND")
    print("-" * 65)

    for timeframe in ["4h", "1h", "15m"]:
        item = trend_result[f"trend_{timeframe}"]
        print(
            f"{timeframe.upper():5} : "
            f"{item['trend']:8} ({item['score']:+d})"
        )

    print(f"TOTAL SCORE : {trend_result['total_score']:+d}")
    print(f"FINAL TREND : {trend_result['final_trend']}")

    print("\nENTRY TIMEFRAME : 1M")
    print("-" * 65)
    print(f"EMA 8           : {signal_result.get('ema8')}")
    print(f"EMA 21          : {signal_result.get('ema21')}")
    print(f"EMA 185         : {signal_result.get('ema185')}")
    print(f"CROSSOVER       : {signal_result['crossover_signal']}")
    print(f"FINAL SIGNAL    : {signal_result['final_signal']}")
    print(f"REASON          : {signal_result['entry_reason']}")


def run_forward():
    if REAL_ORDERS_ENABLED:
        raise RuntimeError(
            "Safety check failed: this runner must not send real orders."
        )

    engine = ForwardEngineB()
    last_processed_candle = None

    print("=" * 70)
    print("SOLUSDT STRATEGY B LIVE FORWARD PAPER TRADING")
    print("=" * 70)
    print("Symbol             :", SYMBOL)
    print("Trend Timeframes   : 4H / 1H / 15M")
    print("Entry Timeframe    :", ENTRY_TIMEFRAME)
    print("Entry Indicators   : EMA 8 / EMA 21 / EMA 185")
    print("Initial Balance    : 5000 USDT")
    print("Margin per Entry   : 500 USDT")
    print("Leverage           : 10x")
    print("Risk / Reward      : 1:2")
    print("Equity Kill Switch : 5%")
    print("Mode               : PAPER TRADING")
    print("Real Orders        : DISABLED")
    print("=" * 70)

    recovered = engine.get_account()
    if recovered["open_position"]:
        print("\nRECOVERED OPEN POSITION FROM DATABASE")
        print(recovered["open_position"])
    else:
        print("\nNo open position recovered from database.")

    while True:
        try:
            # 1. Fetch 1M market data and keep closed candles only.
            raw_1m = get_market_data(
                symbol=SYMBOL,
                interval=ENTRY_TIMEFRAME,
                limit=ENTRY_DATA_LIMIT,
            )
            df_1m = prepare_entry_data(raw_1m)

            latest_time = df_1m.iloc[-1]["open_time"]
            latest_time_key = candle_time_string(latest_time)

            # 2. Detect new closed candles.
            if last_processed_candle is None:
                # On restart, if a position was recovered, replay the
                # available closed candles after its entry candle so
                # historical SL/TP/exit conditions are not silently skipped.
                if engine.position is not None:
                    try:
                        entry_timestamp = pd.to_datetime(
                            engine.position.entry_time,
                            utc=True,
                        )
                        new_rows = df_1m[
                            df_1m["open_time"] > entry_timestamp
                        ]
                    except (TypeError, ValueError):
                        # Older/test positions may have non-date entry_time.
                        new_rows = df_1m.tail(1)

                    if new_rows.empty:
                        new_rows = df_1m.tail(0)
                else:
                    # With no recovered position, only evaluate the latest
                    # candle to avoid entering on an old historical crossover.
                    new_rows = df_1m.tail(1)
            else:
                last_timestamp = pd.Timestamp(last_processed_candle)
                new_rows = df_1m[
                    df_1m["open_time"] > last_timestamp
                ]

            if new_rows.empty:
                print(
                    f"\rWaiting for next closed 1M candle... "
                    f"Latest: {latest_time_key}",
                    end="",
                    flush=True,
                )
                time.sleep(POLLING_SECONDS)
                continue

            # 3. Refresh MTF trend when a new 1M candle is available.
            mtf_data = get_multi_timeframe_data(
                symbol=SYMBOL,
                limit=MTF_DATA_LIMIT,
            )
            trend_result = calculate_multi_timeframe_trend(
                df_4h=mtf_data["4h"],
                df_1h=mtf_data["1h"],
                df_15m=mtf_data["15m"],
            )

            rows_to_process = list(new_rows.iterrows())

            print("\n" + "=" * 70)
            print("NEW CLOSED CANDLE(S) DETECTED")
            print("Count :", len(rows_to_process))
            print("Latest:", latest_time_key)
            print("=" * 70)

            for row_number, (_, candle_row) in enumerate(rows_to_process):
                candle_timestamp = candle_time_string(
                    candle_row["open_time"]
                )

                # Calculate signal only from candles up to this candle.
                history_until_candle = df_1m[
                    df_1m["open_time"] <= candle_row["open_time"]
                ].copy()

                signal_result = generate_strategy_b_signal(
                    trend_result=trend_result,
                    df_1m=history_until_candle,
                )

                candle = {
                    "open": float(candle_row["open"]),
                    "high": float(candle_row["high"]),
                    "low": float(candle_row["low"]),
                    "close": float(candle_row["close"]),
                }

                print_signal(trend_result, signal_result)

                # Existing positions use the raw crossover for opposite-exit.
                if engine.position is not None:
                    engine_signal = signal_result["crossover_signal"]
                else:
                    engine_signal = signal_result["final_signal"]

                    # During catch-up, do not open a stale signal from
                    # an older candle. Only the newest candle can open.
                    is_latest_row = (
                        row_number == len(rows_to_process) - 1
                    )
                    if not is_latest_row:
                        last_processed_candle = candle_timestamp
                        continue

                result = engine.process_signal(
                    trend=trend_result["final_trend"],
                    entry_signal=engine_signal,
                    candle=candle,
                    ema21=signal_result.get("ema21"),
                    ema185=signal_result.get("ema185"),
                    candle_time=candle_timestamp,
                )

                print("\nFORWARD ENGINE ACTION")
                print("-" * 65)
                print("Action :", result.get("action"))
                print(
                    "Result :",
                    result.get("result", result.get("reason")),
                )

                action_result = result.get("result")
                if isinstance(action_result, dict):
                    if action_result.get("success") is True:
                        print("\nNEW PAPER POSITION OPENED")
                        print(action_result["position"])
                    elif "pnl" in action_result:
                        print("\nPAPER POSITION CLOSED")
                        print("Side       :", action_result["side"])
                        print("Entry      :", action_result["entry_price"])
                        print("Exit       :", action_result["exit_price"])
                        print("PnL        :", action_result["pnl"])
                        print("Reason     :", action_result["reason"])

                last_processed_candle = candle_timestamp
                print_account(engine, market_price=candle["close"])

            print("\nTOTAL CLOSED TRADES :", len(engine.trade_history))
            print("LAST PROCESSED      :", last_processed_candle)
            print("=" * 70)

        except KeyboardInterrupt:
            print("\nForward Trading dihentikan oleh pengguna.")
            break

        except Exception as error:
            print("\nFORWARD ENGINE ERROR")
            print(type(error).__name__, str(error))
            print("Runner akan mencoba kembali pada siklus berikutnya.")

        time.sleep(POLLING_SECONDS)


if __name__ == "__main__":
    run_forward()
