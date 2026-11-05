import unittest
from unittest.mock import patch

from strategies.strategy_b import generate_strategy_b_signal


class TestStrategyBSignalIntegration(unittest.TestCase):

    def setUp(self):
        self.df_1m = None

    def make_trend(self, trend, score):
        return {
            "final_trend": trend,
            "total_score": score,
            "trend_4h": {"trend": trend, "score": score},
            "trend_1h": {"trend": trend, "score": score},
            "trend_15m": {"trend": trend, "score": score},
        }

    def make_entry(self, signal):
        return {
            "signal": signal,
            "reason": f"Mock crossover: {signal}",
            "ema8": 101.0,
            "ema21": 100.0,
            "ema185": 99.0,
            "close": 102.0,
        }

    def run_case(self, trend, score, crossover):
        with patch(
            "strategies.strategy_b.calculate_triple_ema_signal",
            return_value=self.make_entry(crossover),
        ):
            return generate_strategy_b_signal(
                trend_result=self.make_trend(trend, score),
                df_1m=self.df_1m,
            )

    def test_bullish_long_approved(self):
        result = self.run_case("BULLISH", 2, "LONG")
        self.assertEqual(result["final_signal"], "LONG")

    def test_bearish_short_approved(self):
        result = self.run_case("BEARISH", -2, "SHORT")
        self.assertEqual(result["final_signal"], "SHORT")

    def test_bullish_short_rejected(self):
        result = self.run_case("BULLISH", 2, "SHORT")
        self.assertEqual(result["final_signal"], "WAIT")

    def test_bearish_long_rejected(self):
        result = self.run_case("BEARISH", -2, "LONG")
        self.assertEqual(result["final_signal"], "WAIT")

    def test_neutral_long_rejected(self):
        result = self.run_case("NEUTRAL", 0, "LONG")
        self.assertEqual(result["final_signal"], "WAIT")

    def test_neutral_short_rejected(self):
        result = self.run_case("NEUTRAL", 0, "SHORT")
        self.assertEqual(result["final_signal"], "WAIT")


if __name__ == "__main__":
    print("=" * 65)
    print("STRATEGY B SIGNAL INTEGRATION TEST")
    print("=" * 65)
    unittest.main(verbosity=2)
