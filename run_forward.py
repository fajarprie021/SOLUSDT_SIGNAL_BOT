
import time

from data.binance_data import get_market_data
from indicators.technical import calculate_indicators

from paper_trading.forward_engine import (
    process_new_candles
)

from paper_trading.database import (
    load_state,
    get_trade_history
)


SYMBOL = "SOLUSDT"
TIMEFRAME = "1m"

POLLING_SECONDS = 15


def run_forward():

    print("=" * 60)
    print("SOLUSDT LIVE FORWARD PAPER TRADING")
    print("=" * 60)

    print("Market       :", SYMBOL)
    print("Timeframe    :", TIMEFRAME)
    print("Initial Cash : 5000 USDT")
    print("Mode         : PAPER ONLY")
    print("Real Orders  : DISABLED")
    print("=" * 60)

    while True:

        try:

            # 1. Fetch closed market candles
            df = get_market_data(
                symbol=SYMBOL,
                interval=TIMEFRAME,
                limit=200
            )

            # 2. Calculate indicators
            df = calculate_indicators(df)

            # 3. Process only new candles
            result = process_new_candles(df)

            # 4. Read saved state
            state = load_state()

            history = get_trade_history()

            print("\n" + "-" * 60)

            print("LATEST CANDLE :", df.iloc[-1]["open_time"])

            print("STATUS        :", result["status"])

            print("NEW CANDLES   :", result["processed"])

            print("NEW TRADES    :", len(result["new_trades"]))

            if state:

                print(
                    "BALANCE       :",
                    f"{state['balance']:.2f} USDT"
                )

                if state["position"]:

                    position = state["position"]

                    print(
                        "OPEN POSITION :",
                        position["side"]
                    )

                    print(
                        "ENTRY PRICE   :",
                        position["entry"]
                    )

                    print(
                        "STOP LOSS     :",
                        position["stop_loss"]
                    )

                    print(
                        "TAKE PROFIT   :",
                        position["take_profit"]
                    )

                else:

                    print("OPEN POSITION : NONE")

            print(
                "TOTAL CLOSED TRADES :",
                len(history)
            )

            for trade in result["new_trades"]:

                print("\nNEW TRADE CLOSED")

                print("Side       :", trade["side"])
                print("Entry      :", trade["entry_price"])
                print("Exit       :", trade["exit_price"])
                print("Net PnL    :", round(trade["net_pnl"], 4))
                print("Exit Reason:", trade["exit_reason"])

            print("-" * 60)

        except KeyboardInterrupt:

            print("\nForward trading dihentikan.")
            break

        except Exception as e:

            print("\nFORWARD ENGINE ERROR:", str(e))

        print(
            f"\nMenunggu {POLLING_SECONDS} detik..."
        )

        time.sleep(POLLING_SECONDS)


if __name__ == "__main__":

    run_forward()
