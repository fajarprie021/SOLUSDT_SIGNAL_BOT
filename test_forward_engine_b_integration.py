from pathlib import Path
import unittest

import paper_trading.database_b as db

# Use a dedicated database. Do not touch the production Strategy B database.
db.DB_PATH = (
    Path(__file__).resolve().parent
    / "strategy_b_forward_integration_test.db"
)

from paper_trading.forward_engine_b import ForwardEngineB


class TestForwardEngineBIntegration(unittest.TestCase):

    def setUp(self):
        db.initialize_database()
        db.save_account_state(
            balance=5000.0,
            position=None,
        )
        db.save_kill_switch(False)

        with db.get_connection() as conn:
            conn.execute("DELETE FROM trade_history")
            conn.commit()

        self.engine = ForwardEngineB()

    def open_long(self):
        result = self.engine.process_signal(
            trend="BULLISH",
            entry_signal="LONG",
            candle={
                "open": 100.0,
                "high": 100.5,
                "low": 99.5,
                "close": 100.0,
            },
            ema21=99.0,
            ema185=98.0,
            candle_time="TEST_LONG_ENTRY",
        )
        self.assertEqual(result["action"], "OPEN")
        self.assertTrue(result["result"]["success"])
        return result

    def open_short(self):
        result = self.engine.process_signal(
            trend="BEARISH",
            entry_signal="SHORT",
            candle={
                "open": 100.0,
                "high": 100.5,
                "low": 99.5,
                "close": 100.0,
            },
            ema21=101.0,
            ema185=102.0,
            candle_time="TEST_SHORT_ENTRY",
        )
        self.assertEqual(result["action"], "OPEN")
        self.assertTrue(result["result"]["success"])
        return result

    def test_01_open_long(self):
        result = self.open_long()
        position = result["result"]["position"]

        self.assertEqual(position["side"], "LONG")
        self.assertEqual(position["margin"], 500.0)
        self.assertEqual(position["notional"], 5000.0)
        self.assertEqual(position["stop_loss"], 99.0)
        self.assertEqual(position["take_profit"], 102.0)

    def test_02_open_short(self):
        result = self.open_short()
        position = result["result"]["position"]

        self.assertEqual(position["side"], "SHORT")
        self.assertEqual(position["margin"], 500.0)
        self.assertEqual(position["notional"], 5000.0)
        self.assertEqual(position["stop_loss"], 101.0)
        self.assertEqual(position["take_profit"], 98.0)

    def test_03_opposite_crossover_closes_long(self):
        self.open_long()

        result = self.engine.process_signal(
            trend="BULLISH",
            entry_signal="SHORT",
            candle={
                "open": 100.5,
                "high": 101.0,
                "low": 100.0,
                "close": 100.5,
            },
            ema21=99.2,
            ema185=98.0,
            candle_time="TEST_LONG_OPPOSITE",
        )

        self.assertEqual(result["action"], "MONITOR")
        trade = result["result"]
        self.assertEqual(trade["reason"], "OPPOSITE_CROSSOVER")
        self.assertIsNone(self.engine.position)

    def test_04_opposite_crossover_closes_short(self):
        self.open_short()

        result = self.engine.process_signal(
            trend="BEARISH",
            entry_signal="LONG",
            candle={
                "open": 99.5,
                "high": 100.0,
                "low": 99.0,
                "close": 99.5,
            },
            ema21=100.8,
            ema185=102.0,
            candle_time="TEST_SHORT_OPPOSITE",
        )

        self.assertEqual(result["action"], "MONITOR")
        trade = result["result"]
        self.assertEqual(trade["reason"], "OPPOSITE_CROSSOVER")
        self.assertIsNone(self.engine.position)

    def test_05_long_stop_loss(self):
        self.open_long()

        result = self.engine.process_signal(
            trend="BULLISH",
            entry_signal="WAIT",
            candle={
                "open": 99.5,
                "high": 100.0,
                "low": 98.8,
                "close": 99.2,
            },
            ema21=99.0,
            ema185=98.0,
            candle_time="TEST_LONG_SL",
        )

        trade = result["result"]
        self.assertEqual(trade["reason"], "STOP_LOSS")
        self.assertEqual(trade["exit_price"], 99.0)
        self.assertIsNone(self.engine.position)

    def test_06_short_stop_loss(self):
        self.open_short()

        result = self.engine.process_signal(
            trend="BEARISH",
            entry_signal="WAIT",
            candle={
                "open": 100.5,
                "high": 101.2,
                "low": 100.0,
                "close": 100.8,
            },
            ema21=101.0,
            ema185=102.0,
            candle_time="TEST_SHORT_SL",
        )

        trade = result["result"]
        self.assertEqual(trade["reason"], "STOP_LOSS")
        self.assertEqual(trade["exit_price"], 101.0)
        self.assertIsNone(self.engine.position)

    def test_07_long_take_profit(self):
        self.open_long()

        result = self.engine.process_signal(
            trend="BULLISH",
            entry_signal="WAIT",
            candle={
                "open": 101.0,
                "high": 102.2,
                "low": 100.5,
                "close": 102.1,
            },
            ema21=99.5,
            ema185=98.0,
            candle_time="TEST_LONG_TP",
        )

        trade = result["result"]
        self.assertEqual(trade["reason"], "TAKE_PROFIT")
        self.assertEqual(trade["exit_price"], 102.0)
        self.assertAlmostEqual(trade["pnl"], 100.0, places=6)
        self.assertIsNone(self.engine.position)

    def test_08_short_take_profit(self):
        self.open_short()

        result = self.engine.process_signal(
            trend="BEARISH",
            entry_signal="WAIT",
            candle={
                "open": 99.0,
                "high": 99.5,
                "low": 97.8,
                "close": 98.0,
            },
            ema21=100.5,
            ema185=102.0,
            candle_time="TEST_SHORT_TP",
        )

        trade = result["result"]
        self.assertEqual(trade["reason"], "TAKE_PROFIT")
        self.assertEqual(trade["exit_price"], 98.0)
        self.assertAlmostEqual(trade["pnl"], 100.0, places=6)
        self.assertIsNone(self.engine.position)


if __name__ == "__main__":
    print("=" * 70)
    print("STRATEGY B FORWARD ENGINE INTEGRATION TEST")
    print("DATABASE: strategy_b_forward_integration_test.db")
    print("REAL ORDERS: DISABLED")
    print("=" * 70)

    unittest.main(verbosity=2)
