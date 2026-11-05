
from paper_trading.risk_manager_b import (
    calculate_position_size,
    validate_new_position,
    INITIAL_BALANCE,
    LEVERAGE,
    MARGIN_ALLOCATION
)

print("=" * 65)
print("STRATEGY B RISK MANAGEMENT TEST")
print("=" * 65)

# ==========================================
# 1. INITIAL BALANCE
# ==========================================

balance = INITIAL_BALANCE

print("\nINITIAL BALANCE")
print(f"Balance       : {balance:.2f} USDT")
print(f"Leverage      : {LEVERAGE}x")
print(f"Margin Rate   : {MARGIN_ALLOCATION * 100:.0f}%")

# ==========================================
# 2. CALCULATE POSITION SIZE
# ==========================================

position = calculate_position_size(balance)

print("\nPOSITION CALCULATION")
print("-" * 65)

print(
    f"Available Balance : "
    f"{position['available_balance']:.2f} USDT"
)

print(
    f"Margin            : "
    f"{position['margin']:.2f} USDT"
)

print(
    f"Leverage          : "
    f"{position['leverage']}x"
)

print(
    f"Notional          : "
    f"{position['notional']:.2f} USDT"
)

# ==========================================
# 3. VALIDATE NEW POSITION
# ==========================================

print("\nPOSITION VALIDATION")
print("-" * 65)

result = validate_new_position(
    available_balance=balance,
    open_positions=[]
)

print("Allowed :", result["allowed"])
print("Reason  :", result["reason"])

# ==========================================
# 4. TEST EXISTING POSITION
# ==========================================

print("\nEXISTING POSITION TEST")
print("-" * 65)

result_existing = validate_new_position(
    available_balance=balance,
    open_positions=[{"side": "LONG"}]
)

print("Allowed :", result_existing["allowed"])
print("Reason  :", result_existing["reason"])

print("\nRISK MANAGEMENT TEST COMPLETED")
print("=" * 65)
