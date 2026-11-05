from pathlib import Path
import unittest

import paper_trading.database_b as db

# Dedicated test database; production strategy_b.db is not modified.
db.DB_PATH = (
    Path(__file__).resolve().parent
    / "strategy_b_safety_integration_test.db"
)

from paper_trading.forward_engine_b import ForwardEngineB


class TestForwardEngineBSafety(unittest.TestCase):

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
        result = self.engine.open_position(
            side="LONG",
            entry_price=100.0,
            ema21=99.0,
            ema185=98.0,
            candle_time="SAFETY_TEST_LONG_ENTRY",
        )
        self.assertTrue(result["success"])
        return result

    def open_short(self):
        result = self.engine.open_position(
            side="SHORT",
            entry_price=100.0,
            ema21=101.0,
            ema185=102.0,
            candle_time="SAFETY_TEST_SHORT_ENTRY",
        )
        self.assertTrue(result["success"])
        return result

    def test_01_long_trailing_stop_moves_up_only(self):
        self.open_long()

        self.engine.update_trailing_stop(100.0)
        self.assertAlmostEqual(self.engine.position.stop_loss, 100.0)

        # A lower EMA21 must not loosen a LONG stop.
        self.engine.update_trailing_stop(99.5)
        self.assertAlmostEqual(self.engine.position.stop_loss, 100.0)

    def test_02_short_trailing_stop_moves_down_only(self):
        self.open_short()

        self.engine.update_trailing_stop(100.0)
        self.assertAlmostEqual(self.engine.position.stop_loss, 100.0)

        # A higher EMA21 must not loosen a SHORT stop.
        self.engine.update_trailing_stop(100.5)
        self.assertAlmostEqual(self.engine.position.stop_loss, 100.0)

    def test_03_long_trailing_stop_can_close_position(self):
        self.open_long()

        # Move trailing stop from 99 to 100.
        self.engine.update_trailing_stop(100.0)

        result = self.engine.monitor_position(
            candle={
                "open": 100.2,
                "high": 100.5,
                "low": 99.8,
                "close": 100.1,
            },
            ema21=100.0,
            ema185=98.0,
            opposite_signal="WAIT",
        )

        self.assertEqual(result["reason"], "STOP_LOSS")
        self.assertAlmostEqual(result["exit_price"], 100.0)
        self.assertIsNone(self.engine.position)

    def test_04_short_trailing_stop_can_close_position(self):
        self.open_short()

        # Move trailing stop from 101 to 100.
        self.engine.update_trailing_stop(100.0)

        result = self.engine.monitor_position(
            candle={
                "open": 99.8,
                "high": 100.2,
                "low": 99.5,
                "close": 99.9,
            },
            ema21=100.0,
            ema185=102.0,
            opposite_signal="WAIT",
        )

        self.assertEqual(result["reason"], "STOP_LOSS")
        self.assertAlmostEqual(result["exit_price"], 100.0)
        self.assertIsNone(self.engine.position)

    def test_05_restart_recovers_open_long_position(self):
        self.open_long()

        recovered_engine = ForwardEngineB()

        self.assertIsNotNone(recovered_engine.position)
        self.assertEqual(recovered_engine.position.side, "LONG")
        self.assertAlmostEqual(
            recovered_engine.position.entry_price,
            100.0,
        )
        self.assertAlmostEqual(
            recovered_engine.position.stop_loss,
            99.0,
        )

    def test_06_restart_recovers_open_short_position(self):
        self.open_short()

        recovered_engine = ForwardEngineB()

        self.assertIsNotNone(recovered_engine.position)
        self.assertEqual(recovered_engine.position.side, "SHORT")
        self.assertAlmostEqual(
            recovered_engine.position.entry_price,
            100.0,
        )
        self.assertAlmostEqual(
            recovered_engine.position.stop_loss,
            101.0,
        )

    def test_07_kill_switch_blocks_new_entry(self):
        self.engine.balance = 4700.0
        self.engine.save_state()

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
            candle_time="KILL_SWITCH_BLOCK_TEST",
        )

        self.assertEqual(result["action"], "BLOCKED")
        self.assertTrue(self.engine.kill_switch_active)
        self.assertIsNone(self.engine.position)

    def test_08_kill_switch_persists_after_restart(self):
        self.engine.balance = 4700.0
        self.engine.save_state()
        self.engine.check_equity_kill_switch()

        recovered_engine = ForwardEngineB()

        self.assertTrue(recovered_engine.kill_switch_active)

    def test_09_kill_switch_reset_requires_no_open_position(self):
        self.open_long()

        result = self.engine.reset_kill_switch()

        self.assertFalse(result["success"])
        self.assertEqual(
            result["reason"],
            "Close open position before reset.",
        )

    def test_10_kill_switch_reset_after_recovery(self):
        self.engine.balance = 4800.0
        self.engine.kill_switch_active = True
        self.engine.save_state()

        result = self.engine.reset_kill_switch()

        self.assertTrue(result["success"])
        self.assertFalse(self.engine.kill_switch_active)


if __name__ == "__main__":
    print("=" * 70)
    print("STRATEGY B SAFETY & RECOVERY INTEGRATION TEST")
    print("DATABASE: strategy_b_safety_integration_test.db")
    print("REAL ORDERS: DISABLED")
    print("=" * 70)

    unittest.main(verbosity=2)
