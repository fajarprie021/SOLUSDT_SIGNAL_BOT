
from pathlib import Path

import paper_trading.database_b as db

# ==========================================
# USE DEDICATED TEST DATABASE
# ==========================================

db.DB_PATH = (
    Path(__file__).resolve().parent
    / "strategy_b_test.db"
)

from paper_trading.forward_engine_b import ForwardEngineB


print("=" * 65)
print("STRATEGY B FORWARD ENGINE TEST")
print("=" * 65)


# ==========================================
# RESET DATABASE BEFORE ENGINE CREATION
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


# ==========================================
# CREATE ENGINE AFTER RESET
# ==========================================

engine = ForwardEngineB()

# ==========================================
# 1. INITIAL ACCOUNT
# ==========================================

print("\n[1] INITIAL ACCOUNT")

print(engine.get_account())

# ==========================================
# 2. OPEN LONG POSITION
# ==========================================

print("\n[2] TEST OPEN LONG")

result = engine.open_position(
    side="LONG",
    entry_price=100.0,
    ema21=99.0,
    ema185=98.0,
    candle_time="TEST_CANDLE_001"
)

print(result)

assert result["success"] is True

# Expected:
# Margin   = 500 USDT
# Notional = 5000 USDT
# Quantity = 50 SOL
# SL       = 99
# TP       = 102

# ==========================================
# 3. TEST PREVENT SECOND POSITION
# ==========================================

print("\n[3] TEST MAXIMUM POSITION")

second = engine.open_position(
    side="LONG",
    entry_price=100.0,
    ema21=99.0,
    ema185=98.0,
    candle_time="TEST_CANDLE_002"
)

print(second)

assert second["success"] is False

# ==========================================
# 4. TEST TAKE PROFIT
# ==========================================

print("\n[4] TEST TAKE PROFIT")

trade = engine.monitor_position(
    candle={
        "high": 102.1,
        "low": 99.5,
        "close": 101.8
    },
    ema21=99.0,
    ema185=98.0,
    opposite_signal="WAIT"
)

print(trade)

assert trade["reason"] == "TAKE_PROFIT"

# Expected PnL:
# (102 - 100) x 50 = 100 USDT

# ==========================================
# 5. CHECK FINAL ACCOUNT
# ==========================================

print("\n[5] FINAL ACCOUNT")

account = engine.get_account()

print(account)

assert round(engine.balance, 2) == 5100.00

print("\nTRADE HISTORY")

for item in engine.trade_history:
    print(item)

print("\nALL FORWARD ENGINE TESTS PASSED")
print("=" * 65)
