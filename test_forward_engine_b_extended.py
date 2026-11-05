from pathlib import Path
import sqlite3
import paper_trading.database_b as db

def reset_test_account():

    db.initialize_database()

    db.save_account_state(
        balance=5000.0,
        position=None
    )

    with db.get_connection() as conn:

        conn.execute("DELETE FROM trade_history")

        conn.commit()

db.DB_PATH = (
    Path(__file__).resolve().parent
    / "strategy_b_test.db"
)

from paper_trading.forward_engine_b import ForwardEngineB


def test_long_stop_loss():
    
    reset_test_account()

    engine = ForwardEngineB()

    engine.open_position(
        side="LONG",
        entry_price=100,
        ema21=99,
        ema185=98,
        candle_time="TEST_LONG_SL"
    )

    result = engine.monitor_position(
        candle={
            "high": 100,
            "low": 98.5,
            "close": 98.8
        },
        ema21=99,
        ema185=98,
        opposite_signal="WAIT"
    )

    assert result["reason"] == "STOP_LOSS"
    assert round(engine.balance, 2) == 4950.00

    print("LONG STOP LOSS: PASSED")


def test_short_take_profit():

    reset_test_account()

    engine = ForwardEngineB()

    engine.open_position(
        side="SHORT",
        entry_price=100,
        ema21=101,
        ema185=102,
        candle_time="TEST_SHORT_TP"
    )

    result = engine.monitor_position(
        candle={
            "high": 99,
            "low": 97.5,
            "close": 98
        },
        ema21=101,
        ema185=102,
        opposite_signal="WAIT"
    )

    assert result["reason"] == "TAKE_PROFIT"
    assert round(engine.balance, 2) == 5100.00

    print("SHORT TAKE PROFIT: PASSED")


def test_opposite_crossover():

    reset_test_account()

    engine = ForwardEngineB()

    engine.open_position(
        side="LONG",
        entry_price=100,
        ema21=99,
        ema185=98,
        candle_time="TEST_OPPOSITE"
    )

    result = engine.monitor_position(
        candle={
            "high": 100.5,
            "low": 99.5,
            "close": 100
        },
        ema21=99,
        ema185=98,
        opposite_signal="SHORT"
    )

    assert result["reason"] == "OPPOSITE_CROSSOVER"

    print("OPPOSITE CROSSOVER: PASSED")


def test_trailing_stop_long():

    reset_test_account()

    engine = ForwardEngineB()

    engine.open_position(
        side="LONG",
        entry_price=100,
        ema21=99,
        ema185=98,
        candle_time="TEST_TRAILING"
    )

    engine.update_trailing_stop(99.5)

    assert engine.position.stop_loss == 99.5

    # Stop loss must never move downward.
    engine.update_trailing_stop(99.2)

    assert engine.position.stop_loss == 99.5

    print("LONG TRAILING STOP: PASSED")


if __name__ == "__main__":

    print("=" * 60)
    print("FORWARD ENGINE EXTENDED TEST")
    print("=" * 60)

    test_long_stop_loss()
    test_short_take_profit()
    test_opposite_crossover()
    test_trailing_stop_long()

    print("=" * 60)
    print("ALL EXTENDED TESTS PASSED")
    print("=" * 60)
