
# ==========================================
# STRATEGY B RISK CONFIGURATION
# ==========================================

INITIAL_BALANCE = 5000.0

LEVERAGE = 10

MARGIN_ALLOCATION = 0.10

MAX_OPEN_POSITIONS = 1


# ==========================================
# POSITION SIZING
# ==========================================

def calculate_position_size(available_balance):

    margin = available_balance * MARGIN_ALLOCATION

    notional = margin * LEVERAGE

    quantity = None

    return {
        "available_balance": available_balance,
        "margin": margin,
        "leverage": LEVERAGE,
        "notional": notional,
        "quantity": quantity
    }


# ==========================================
# POSITION VALIDATION
# ==========================================

def validate_new_position(
    available_balance,
    open_positions
):

    if len(open_positions) >= MAX_OPEN_POSITIONS:
        return {
            "allowed": False,
            "reason": "Position already open."
        }

    if available_balance <= 0:
        return {
            "allowed": False,
            "reason": "Insufficient available balance."
        }

    position = calculate_position_size(
        available_balance
    )

    if position["margin"] > available_balance:
        return {
            "allowed": False,
            "reason": "Insufficient margin."
        }

    return {
        "allowed": True,
        "reason": "Position approved.",
        "position": position
    }
