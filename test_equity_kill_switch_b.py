
from pathlib import Path

import paper_trading.database_b as db

# ==========================================
# DEDICATED TEST DATABASE
# ==========================================

db.DB_PATH = (
    Path(__file__).resolve().parent
    / "strategy_b_kill_test.db"
)

from paper_trading.forward_engine_b import ForwardEngineB


print("=" * 65)
print("STRATEGY B EQUITY KILL SWITCH TEST")
print("=" * 65)


# ==========================================
# RESET TEST DATABASE
# ==========================================

db.initialize_database()

db.save_account_state(
    balance=5000.0,
    position=None
)

db.save_kill_switch(False)

with db.get_connection() as conn:
    conn.execute("DELETE FROM trade_history")
    conn.commit()

print("\nTEST DATABASE RESET: PASSED")


# ==========================================
# TEST 1: NORMAL EQUITY
# ==========================================

engine = ForwardEngineB()

assert engine.balance == 5000.0

assert engine.check_equity_kill_switch() is False

print("TEST 1 NORMAL EQUITY: PASSED")


# ==========================================
# TEST 2: KILL SWITCH ACTIVATION
# ==========================================

engine.balance = 4749.0

assert engine.check_equity_kill_switch() is True

assert engine.kill_switch_active is True

print("TEST 2 KILL SWITCH ACTIVATION: PASSED")


# ==========================================
# TEST 3: BLOCK NEW POSITION
# ==========================================

result = engine.open_position(
    side="LONG",
    entry_price=100.0,
    ema21=99.0,
    ema185=98.0,
    candle_time="KILL_TEST"
)

assert result["success"] is False

assert engine.position is None

print("TEST 3 NEW ENTRY BLOCKED: PASSED")


# ==========================================
# TEST 4: PERSISTENCE AFTER RESTART
# ==========================================

del engine

engine = ForwardEngineB()

assert engine.kill_switch_active is True

print("TEST 4 RESTART PERSISTENCE: PASSED")


# ==========================================
# TEST 5: KILL SWITCH STATUS
# ==========================================

status = engine.get_kill_switch_status()

print("\nKILL SWITCH STATUS:")
print(status)

assert status["active"] is True

assert status["new_entries_allowed"] is False

assert status["equity"] == 4749.0

print("\nTEST 5 STATUS VALIDATION: PASSED")


# ==========================================
# FINAL RESULT
# ==========================================

print("\n" + "=" * 65)

print("ALL KILL SWITCH TESTS PASSED")

print("=" * 65)
