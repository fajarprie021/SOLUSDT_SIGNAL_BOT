
from pathlib import Path

import paper_trading.database_b as db

# Dedicated database for this test
db.DB_PATH = (
    Path(__file__).resolve().parent
    / "strategy_b_recovery_test.db"
)

from paper_trading.forward_engine_b import ForwardEngineB


print("=" * 65)
print("STRATEGY B RESTART RECOVERY TEST")
print("=" * 65)


# ==========================================
# 1. RESET TEST DATABASE
# ==========================================

db.initialize_database()

db.save_account_state(
    balance=5000.0,
    position=None
)

with db.get_connection() as conn:
    conn.execute("DELETE FROM trade_history")
    conn.commit()

print("\n[1] TEST DATABASE RESET: PASSED")


# ==========================================
# 2. CREATE ENGINE
# ==========================================

engine_1 = ForwardEngineB()

print("\n[2] INITIAL ACCOUNT")

print(engine_1.get_account())


# ==========================================
# 3. OPEN LONG POSITION
# ==========================================

result = engine_1.open_position(
    side="LONG",
    entry_price=100.0,
    ema21=99.0,
    ema185=98.0,
    candle_time="RECOVERY_TEST_001"
)

assert result["success"] is True

print("\n[3] OPEN LONG POSITION: PASSED")

print(result)


# ==========================================
# 4. SIMULATE ENGINE RESTART
# ==========================================

del engine_1

engine_2 = ForwardEngineB()

print("\n[4] ENGINE RESTARTED")


# ==========================================
# 5. VERIFY RESTORED POSITION
# ==========================================

position = engine_2.position

assert position is not None

assert position.side == "LONG"

assert position.entry_price == 100.0

assert position.quantity == 50.0

assert position.stop_loss == 99.0

assert position.take_profit == 102.0

print("\n[5] POSITION RECOVERY: PASSED")

print({
    "side": position.side,
    "entry_price": position.entry_price,
    "quantity": position.quantity,
    "stop_loss": position.stop_loss,
    "take_profit": position.take_profit
})


# ==========================================
# 6. VERIFY ACCOUNT BALANCE
# ==========================================

account = engine_2.get_account()

assert account["balance"] == 5000.0

assert account["margin_used"] == 500.0

assert account["available_balance"] == 4500.0

print("\n[6] ACCOUNT RECOVERY: PASSED")

print(account)


# ==========================================
# 7. VERIFY SECOND POSITION BLOCKED
# ==========================================

second = engine_2.open_position(
    side="LONG",
    entry_price=101.0,
    ema21=100.0,
    ema185=99.0,
    candle_time="RECOVERY_TEST_002"
)

assert second["success"] is False

print("\n[7] DUPLICATE POSITION PROTECTION: PASSED")


# ==========================================
# FINAL RESULT
# ==========================================

print("\n" + "=" * 65)

print("ALL RESTART RECOVERY TESTS PASSED")

print("=" * 65)
