
from data.multi_timeframe_data import (
    get_multi_timeframe_data,
    display_multi_timeframe_data
)

from strategies.trend_filter import (
    calculate_multi_timeframe_trend
)


print("=" * 65)
print("SOLUSDT MULTI-TIMEFRAME TEST")
print("=" * 65)

try:

    # 1. Mengambil data Binance Futures
    market_data = get_multi_timeframe_data(
        symbol="SOLUSDT",
        limit=300
    )

    # 2. Menampilkan informasi candle
    display_multi_timeframe_data(
        market_data
    )

    # 3. Menghitung voting trend
    result = calculate_multi_timeframe_trend(
        df_4h=market_data["4h"],
        df_1h=market_data["1h"],
        df_15m=market_data["15m"]
    )

    # 4. Menampilkan hasil voting
    print("\nMULTI-TIMEFRAME TREND RESULT")
    print("=" * 65)

    for timeframe in ["4h", "1h", "15m"]:

        trend = result[f"trend_{timeframe}"]

        print(
            f"{timeframe.upper():5} : "
            f"{trend['trend']:8} "
            f"({trend['score']:+d})"
        )

    print("-" * 65)

    print(
        "TOTAL SCORE :",
        result["total_score"]
    )

    print(
        "FINAL TREND :",
        result["final_trend"]
    )

    print("=" * 65)

except Exception as e:

    print("\nMULTI-TIMEFRAME ERROR:")
    print(e)
