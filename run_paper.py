from data.binance_data import get_market_data

from indicators.technical import calculate_indicators

from paper_trading.simulator import (
    run_simulation,
    calculate_statistics
)


SYMBOL = "SOLUSDT"
TIMEFRAME = "1m"


def main():

    print("=" * 60)
    print("SOLUSDT PAPER TRADING SIMULATOR")
    print("=" * 60)

    # 1. Ambil data historis
    print("\nMengambil data Binance Futures...")

    df = get_market_data(
        symbol=SYMBOL,
        interval=TIMEFRAME,
        limit=1000
    )

    if len(df) < 100:
        print("Data tidak mencukupi untuk simulasi.")
        return

    # 2. Hitung indikator
    print("Menghitung indikator EMA, RSI, MACD...")

    df = calculate_indicators(df)

    # 3. Jalankan simulasi
    print("Menjalankan paper trading...")

    result = run_simulation(df)

    # 4. Hitung statistik
    stats = calculate_statistics(result)

    print("\n" + "=" * 60)
    print("PAPER TRADING PERFORMANCE")
    print("=" * 60)

    print(
        f"Initial Balance : "
        f"{result['initial_balance']:.2f} USDT"
    )

    print(
        f"Final Balance   : "
        f"{result['final_balance']:.2f} USDT"
    )

    print(
        f"Net Profit      : "
        f"{stats['net_profit']:.2f} USDT"
    )

    print(
        f"Total Trades    : "
        f"{stats['total_trades']}"
    )

    print(
        f"Win Rate        : "
        f"{stats['win_rate']:.2f}%"
    )

    print(
        f"Profit Factor   : "
        f"{stats['profit_factor']:.2f}"
    )

    print(
        f"Total Profit    : "
        f"{stats['total_profit']:.2f} USDT"
    )

    print(
        f"Total Loss      : "
        f"{stats['total_loss']:.2f} USDT"
    )

    print(
        f"Max Drawdown    : "
        f"{stats['max_drawdown']:.2f}%"
    )

    # 5. Riwayat transaksi
    print("\n" + "=" * 60)
    print("TRADE HISTORY")
    print("=" * 60)

    if result["trades"]:

        trade_df = pd.DataFrame(result["trades"])

        print(
            trade_df[
                [
                    "side",
                    "entry_price",
                    "exit_price",
                    "net_pnl",
                    "exit_reason"
                ]
            ].to_string(index=False)
        )

    else:
        print("Belum ada transaksi.")

    print("\nMODE: PAPER TRADING")
    print("REAL ORDER: DISABLED")
    print("=" * 60)


if __name__ == "__main__":

    import pandas as pd

    try:
        main()

    except Exception as e:
        print("\nPAPER TRADING ERROR:", str(e))