
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime, timezone

from paper_trading.database_b import (
    initialize_database,
    load_account_state,
    save_account_state,
    save_trade,
    get_trade_history,
)


# ==================================================
# STRATEGY B CONFIGURATION
# ==================================================

INITIAL_BALANCE = 5000.0

FIXED_MARGIN = 500.0

LEVERAGE = 10

NOTIONAL = FIXED_MARGIN * LEVERAGE

MAX_OPEN_POSITIONS = 1

RISK_REWARD = 2.0


# ==================================================
# POSITION DATA
# ==================================================

@dataclass
class PositionB:

    side: str

    entry_price: float

    quantity: float

    margin: float

    notional: float

    initial_sl: float

    stop_loss: float

    take_profit: float

    entry_time: str

    entry_ema21: float

    entry_ema185: float


# ==================================================
# FORWARD PAPER ENGINE B
# ==================================================

class ForwardEngineB:

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(self):

        initialize_database()

        account = load_account_state()

        self.balance = float(
            account["balance"]
        )

        saved_position = account.get(
            "position"
        )

        if saved_position is not None:

            self.position = PositionB(
                **saved_position
            )

        else:

            self.position = None

        self.trade_history = get_trade_history(
            limit=100000
        )

        self.last_processed_candle = None

    # ==================================================
    # SAVE STATE TO DATABASE
    # ==================================================

    def save_state(self):

        position_data = None

        if self.position is not None:

            position_data = asdict(
                self.position
            )

        save_account_state(
            balance=self.balance,
            position=position_data
        )

    # ==================================================
    # ACCOUNT INFORMATION
    # ==================================================

    def get_account(self):

        unrealized = self.get_unrealized_pnl()

        margin_used = 0.0

        if self.position is not None:

            margin_used = self.position.margin

        equity = self.balance + unrealized

        available_balance = (
            self.balance - margin_used
        )

        return {

            "initial_balance": INITIAL_BALANCE,

            "balance": round(
                self.balance, 4
            ),

            "available_balance": round(
                available_balance, 4
            ),

            "margin_used": round(
                margin_used, 4
            ),

            "unrealized_pnl": round(
                unrealized, 4
            ),

            "equity": round(
                equity, 4
            ),

            "open_position": (
                asdict(self.position)
                if self.position is not None
                else None
            )
        }

    # ==================================================
    # UNREALIZED PNL
    # ==================================================

    def get_unrealized_pnl(self, price=None):

        if self.position is None:

            return 0.0

        if price is None:

            price = self.position.entry_price

        price = float(price)

        pos = self.position

        if pos.side == "LONG":

            return (
                price - pos.entry_price
            ) * pos.quantity

        return (
            pos.entry_price - price
        ) * pos.quantity

    # ==================================================
    # OPEN POSITION
    # ==================================================

    def open_position(
        self,
        side,
        entry_price,
        ema21,
        ema185,
        candle_time
    ):

        # Prevent multiple positions
        if self.position is not None:

            return {
                "success": False,
                "reason": "Position already open."
            }

        # Validate side
        if side not in ["LONG", "SHORT"]:

            return {
                "success": False,
                "reason": "Invalid position side."
            }

        # Convert values
        try:

            entry_price = float(entry_price)

            ema21 = float(ema21)

            ema185 = float(ema185)

        except (TypeError, ValueError):

            return {
                "success": False,
                "reason": "Invalid price or EMA values."
            }

        # Validate numerical values
        if any(
            value <= 0
            for value in [
                entry_price,
                ema21,
                ema185
            ]
        ):

            return {
                "success": False,
                "reason": "Price and EMA must be positive."
            }

        # Check available balance
        if self.balance < FIXED_MARGIN:

            return {
                "success": False,
                "reason": "Insufficient available balance."
            }

        # Validate EMA structure
        if side == "LONG" and not ema21 > ema185:

            return {
                "success": False,
                "reason": "LONG EMA structure invalid."
            }

        if side == "SHORT" and not ema21 < ema185:

            return {
                "success": False,
                "reason": "SHORT EMA structure invalid."
            }

        # Calculate quantity
        quantity = NOTIONAL / entry_price

        # Initial Stop Loss based on EMA21
        initial_sl = ema21

        # Calculate Take Profit
        if side == "LONG":

            if initial_sl >= entry_price:

                return {
                    "success": False,
                    "reason": "LONG stop must be below entry."
                }

            risk_distance = (
                entry_price - initial_sl
            )

            take_profit = (
                entry_price
                + risk_distance * RISK_REWARD
            )

        else:

            if initial_sl <= entry_price:

                return {
                    "success": False,
                    "reason": "SHORT stop must be above entry."
                }

            risk_distance = (
                initial_sl - entry_price
            )

            take_profit = (
                entry_price
                - risk_distance * RISK_REWARD
            )

        # Create position
        self.position = PositionB(

            side=side,

            entry_price=entry_price,

            quantity=quantity,

            margin=FIXED_MARGIN,

            notional=NOTIONAL,

            initial_sl=initial_sl,

            stop_loss=initial_sl,

            take_profit=take_profit,

            entry_time=str(candle_time),

            entry_ema21=ema21,

            entry_ema185=ema185
        )

        # Save position immediately
        self.save_state()

        return {

            "success": True,

            "reason": "Paper position opened.",

            "position": asdict(
                self.position
            )
        }

    # ==================================================
    # UPDATE TRAILING STOP
    # ==================================================

    def update_trailing_stop(self, ema21):

        if self.position is None:

            return

        if ema21 is None:

            return

        try:

            ema21 = float(ema21)

        except (TypeError, ValueError):

            return

        if ema21 <= 0:

            return

        pos = self.position

        old_stop = pos.stop_loss

        # LONG: SL can only move upward
        if pos.side == "LONG":

            if ema21 > pos.stop_loss:

                pos.stop_loss = ema21

        # SHORT: SL can only move downward
        else:

            if ema21 < pos.stop_loss:

                pos.stop_loss = ema21

        # Save only when SL changes
        if pos.stop_loss != old_stop:

            self.save_state()

    # ==================================================
    # CLOSE POSITION
    # ==================================================

    def close_position(
        self,
        exit_price,
        reason
    ):

        if self.position is None:

            return None

        exit_price = float(exit_price)

        pos = self.position

        # Calculate realized PNL
        pnl = self.get_unrealized_pnl(
            exit_price
        )

        # Update account balance
        self.balance += pnl

        # Create trade record
        trade = {

            "side": pos.side,

            "entry_price": pos.entry_price,

            "exit_price": exit_price,

            "quantity": pos.quantity,

            "margin": pos.margin,

            "notional": pos.notional,

            "pnl": round(pnl, 4),

            "reason": reason,

            "entry_time": pos.entry_time,

            "exit_time": datetime.now(
                timezone.utc
            ).isoformat()
        }

        # Save closed trade
        save_trade(trade)

        # Update in-memory history
        self.trade_history.append(trade)

        # Clear open position
        self.position = None

        # Save updated account
        self.save_state()

        return trade

    # ==================================================
    # MONITOR OPEN POSITION
    # ==================================================

    def monitor_position(
        self,
        candle,
        ema21,
        ema185,
        opposite_signal="WAIT"
    ):

        if self.position is None:

            return None

        pos = self.position

        high = float(candle["high"])

        low = float(candle["low"])

        close = float(candle["close"])

        ema185 = float(ema185)

        # IMPORTANT:
        # Check the existing SL/TP first.
        # Do not use the current candle's EMA21
        # to move SL before checking its OHLC.
        #
        # This avoids same-candle look-ahead bias.

        if pos.side == "LONG":

            if low <= pos.stop_loss:

                return self.close_position(
                    pos.stop_loss,
                    "STOP_LOSS"
                )

            if high >= pos.take_profit:

                return self.close_position(
                    pos.take_profit,
                    "TAKE_PROFIT"
                )

        else:

            if high >= pos.stop_loss:

                return self.close_position(
                    pos.stop_loss,
                    "STOP_LOSS"
                )

            if low <= pos.take_profit:

                return self.close_position(
                    pos.take_profit,
                    "TAKE_PROFIT"
                )

        # EMA185 invalidation
        if (
            pos.side == "LONG"
            and close < ema185
        ):

            return self.close_position(
                close,
                "EMA185_INVALIDATION"
            )

        if (
            pos.side == "SHORT"
            and close > ema185
        ):

            return self.close_position(
                close,
                "EMA185_INVALIDATION"
            )

        # Opposite crossover exit
        if (
            pos.side == "LONG"
            and opposite_signal == "SHORT"
        ):

            return self.close_position(
                close,
                "OPPOSITE_CROSSOVER"
            )

        if (
            pos.side == "SHORT"
            and opposite_signal == "LONG"
        ):

            return self.close_position(
                close,
                "OPPOSITE_CROSSOVER"
            )

        # Update trailing SL for NEXT candle
        self.update_trailing_stop(
            ema21
        )

        return {

            "status": "POSITION_OPEN",

            "unrealized_pnl": self.get_unrealized_pnl(
                close
            ),

            "stop_loss": self.position.stop_loss,

            "take_profit": self.position.take_profit
        }

    # ==================================================
    # PROCESS NEW SIGNAL
    # ==================================================

    def process_signal(
        self,
        trend,
        entry_signal,
        candle,
        ema21,
        ema185,
        candle_time
    ):

        # If position exists, monitor it
        if self.position is not None:

            result = self.monitor_position(

                candle=candle,

                ema21=ema21,

                ema185=ema185,

                opposite_signal=entry_signal
            )

            return {

                "action": "MONITOR",

                "result": result,

                "account": self.get_account()
            }

        # All 3 timeframes must agree
        if trend not in [
            "BULLISH",
            "BEARISH"
        ]:

            return {

                "action": "WAIT",

                "reason": "MTF trend is not confirmed.",

                "account": self.get_account()
            }

        # Determine expected direction
        expected_signal = (

            "LONG"
            if trend == "BULLISH"
            else "SHORT"
        )

        # Validate entry signal
        if entry_signal != expected_signal:

            return {

                "action": "WAIT",

                "reason": "Entry signal does not match trend.",

                "account": self.get_account()
            }

        # Open paper position
        result = self.open_position(

            side=expected_signal,

            entry_price=float(
                candle["close"]
            ),

            ema21=ema21,

            ema185=ema185,

            candle_time=candle_time
        )

        return {

            "action": (
                "OPEN"
                if result["success"]
                else "REJECTED"
            ),

            "result": result,

            "account": self.get_account()
        }
