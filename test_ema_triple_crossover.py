
import pandas as pd

from strategies.ema_triple_crossover import (
    calculate_triple_ema_signal
)

print("=" * 65)
print("TRIPLE EMA CROSSOVER TEST")
print("=" * 65)

# Test bullish crossover
bullish = [100.0] * 350

bullish[-2] = 100.0
bullish[-1] = 110.0

df = pd.DataFrame({"close": bullish})

result = calculate_triple_ema_signal(df)

print("\nBULLISH TEST")
print(result)

# Test bearish crossover
bearish = [110.0] * 350

bearish[-2] = 110.0
bearish[-1] = 90.0

df = pd.DataFrame({"close": bearish})

result = calculate_triple_ema_signal(df)

print("\nBEARISH TEST")
print(result)

print("\nTEST COMPLETED")
