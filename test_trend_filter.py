
import pandas as pd
import numpy as np

from strategies.trend_filter import (
    calculate_trend,
    calculate_multi_timeframe_trend
)

# Membuat data simulasi untuk pengujian modul
np.random.seed(42)

def create_test_data(trend="bullish", periods=300):

    if trend == "bullish":
        prices = np.linspace(90, 120, periods)

    elif trend == "bearish":
        prices = np.linspace(120, 90, periods)

    else:
        prices = 100 + np.random.normal(
            0, 0.05, periods
        )

    return pd.DataFrame({
        "close": prices
    })


df_bullish = create_test_data("bullish")
df_bearish = create_test_data("bearish")
df_neutral = create_test_data("neutral")

print("\nTEST INDIVIDUAL TIMEFRAME")

print("Bullish:", calculate_trend(df_bullish))
print("Bearish:", calculate_trend(df_bearish))
print("Neutral:", calculate_trend(df_neutral))

print("\nTEST MULTI-TIMEFRAME")

result = calculate_multi_timeframe_trend(
    df_bullish,
    df_bullish,
    df_bearish
)

print(result)
