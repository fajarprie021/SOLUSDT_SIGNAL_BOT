from data.binance_data import get_market_data
from indicators.technical import calculate_indicators
from strategies.signal import generate_signal


SYMBOL = "SOLUSDT"
TIMEFRAME = "1m"


def run_bot():

    print("=" * 60)
    print("SOLUSDT FUTURES SIGNAL BOT")
    print("=" * 60)

    # 1. Ambil data market
    df = get_market_data(
        symbol=SYMBOL,
        interval=TIMEFRAME,
        limit=200
    )

    if len(df) < 50:
        print("Data candle tidak mencukupi.")
        return

    # 2. Hitung indikator
    df = calculate_indicators(df)

    # 3. Generate signal
    result = generate_signal(df)

    latest = df.iloc[-1]

    print("\nMARKET INFORMATION")
    print("-" * 60)

    print(f"Symbol       : {SYMBOL}")
    print(f"Timeframe    : {TIMEFRAME}")
    print(f"Candle time  : {latest['open_time']}")
    print(f"Last Price   : {latest['close']} USDT")

    print("\nTECHNICAL INDICATORS")
    print("-" * 60)

    print(f"EMA 9        : {latest['ema_9']:.5f}")
    print(f"EMA 21       : {latest['ema_21']:.5f}")
    print(f"RSI 14       : {latest['rsi']:.2f}")
    print(f"MACD         : {latest['macd']:.5f}")
    print(f"MACD Signal  : {latest['macd_signal']:.5f}")
    print(f"MACD Hist    : {latest['macd_hist']:.5f}")

    print("\nTRADING SIGNAL")
    print("=" * 60)

    print(f"SIGNAL : {result['signal']}")
    print(f"REASON : {result['reason']}")

    print("=" * 60)
    print("MODE: SIGNAL ONLY")
    print("ORDER EXECUTION: DISABLED")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_bot()

    except Exception as e:
        print("\nBOT ERROR:", str(e))