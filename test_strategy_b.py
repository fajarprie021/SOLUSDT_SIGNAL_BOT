
from data.multi_timeframe_data import (
    get_multi_timeframe_data,
    remove_incomplete_candles
)

from data.binance_data import get_market_data

from strategies.trend_filter import (
    calculate_multi_timeframe_trend
)

from strategies.strategy_b import (
    generate_strategy_b_signal
)


print("=" * 65)
print("SOLUSDT STRATEGY B TEST")
print("MULTI-TIMEFRAME + TRIPLE EMA")
print("=" * 65)

try:

    # ======================================
    # 1. GET MULTI-TIMEFRAME DATA
    # ======================================

    print("\n[1] Mengambil data multi-timeframe...")

    mtf_data = get_multi_timeframe_data(
        symbol="SOLUSDT",
        limit=300
    )

    # ======================================
    # 2. GET 1 MINUTE DATA
    # ======================================

    print("\n[2] Mengambil data entry 1M...")

    df_1m = get_market_data(
        symbol="SOLUSDT",
        interval="1m",
        limit=500
    )

    df_1m = remove_incomplete_candles(
        df_1m,
        timeframe_seconds=60
    )

    if len(df_1m) < 300:
        raise ValueError(
            "Data 1M tidak mencukupi untuk EMA8/21/185."
        )

    print(
        f"Data 1M: {len(df_1m)} candle tertutup"
    )

    # ======================================
    # 3. CALCULATE MULTI-TIMEFRAME TREND
    # ======================================

    print("\n[3] Menghitung trend voting...")

    trend_result = calculate_multi_timeframe_trend(
        df_4h=mtf_data["4h"],
        df_1h=mtf_data["1h"],
        df_15m=mtf_data["15m"]
    )

    print("\nMULTI-TIMEFRAME RESULT")
    print("=" * 65)

    for timeframe in ["4h", "1h", "15m"]:

        result = trend_result[f"trend_{timeframe}"]

        print(
            f"{timeframe.upper():5}: "
            f"{result['trend']:8} "
            f"({result['score']:+d})"
        )

    print("-" * 65)

    print(
        "TOTAL SCORE :",
        trend_result["total_score"]
    )

    print(
        "FINAL TREND :",
        trend_result["final_trend"]
    )

    # ======================================
    # 4. GENERATE STRATEGY B SIGNAL
    # ======================================

    print(
        "\n[4] Menghitung crossover EMA8/EMA21/EMA185..."
    )

    strategy_result = generate_strategy_b_signal(
        trend_result=trend_result,
        df_1m=df_1m
    )

    # ======================================
    # 5. DISPLAY STRATEGY B RESULT
    # ======================================

    print("\nSTRATEGY B RESULT")
    print("=" * 65)

    print(
        "Market Trend     :",
        strategy_result["market_trend"]
    )

    print(
        "Trend Score      :",
        strategy_result["trend_score"]
    )

    print("-" * 65)

    print(
        "EMA 8            :",
        strategy_result["ema8"]
    )

    print(
        "EMA 21           :",
        strategy_result["ema21"]
    )

    print(
        "EMA 185          :",
        strategy_result["ema185"]
    )

    print("-" * 65)

    print(
        "Crossover Signal :",
        strategy_result["crossover_signal"]
    )

    print(
        "Final Signal     :",
        strategy_result["final_signal"]
    )

    print(
        "Reason           :",
        strategy_result["entry_reason"]
    )

    print("=" * 65)

    print("\nSTRATEGY B TEST COMPLETED")

except Exception as e:

    print("\nSTRATEGY B TEST ERROR:")
    print(type(e).__name__, e)
