
import sqlite3
import json

from pathlib import Path
from datetime import datetime, timezone


DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "paper_trading.db"
)


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                initial_balance REAL NOT NULL,
                balance REAL NOT NULL,
                position_json TEXT,
                last_processed_open_time TEXT,
                session_started_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                side TEXT NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                quantity REAL NOT NULL,
                gross_pnl REAL NOT NULL,
                entry_fee REAL NOT NULL,
                exit_fee REAL NOT NULL,
                net_pnl REAL NOT NULL,
                exit_reason TEXT NOT NULL,
                balance REAL NOT NULL
            )
        """)

        conn.commit()


def initialize_session(latest_open_time):

    initialize_database()

    with get_connection() as conn:

        existing = conn.execute(
            "SELECT * FROM bot_state WHERE id = 1"
        ).fetchone()

        if existing is not None:
            return False

        now = datetime.now(timezone.utc).isoformat()

        conn.execute("""
            INSERT INTO bot_state (
                id,
                initial_balance,
                balance,
                position_json,
                last_processed_open_time,
                session_started_at
            )
            VALUES (1, ?, ?, NULL, ?, ?)
        """, (
            5000.0,
            5000.0,
            str(latest_open_time),
            now
        ))

        conn.commit()

        return True


def load_state():

    initialize_database()

    with get_connection() as conn:

        row = conn.execute(
            "SELECT * FROM bot_state WHERE id = 1"
        ).fetchone()

        if row is None:
            return None

        state = dict(row)

        if state["position_json"]:
            state["position"] = json.loads(
                state["position_json"]
            )
        else:
            state["position"] = None

        return state


def save_candle_result(
    balance,
    position,
    last_processed_open_time,
    trade=None
):

    initialize_database()

    position_json = (
        json.dumps(position)
        if position is not None
        else None
    )

    with get_connection() as conn:

        if trade is not None:

            conn.execute("""
                INSERT INTO trades (
                    side,
                    entry_time,
                    exit_time,
                    entry_price,
                    exit_price,
                    quantity,
                    gross_pnl,
                    entry_fee,
                    exit_fee,
                    net_pnl,
                    exit_reason,
                    balance
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade["side"],
                str(trade["entry_time"]),
                str(trade["exit_time"]),
                trade["entry_price"],
                trade["exit_price"],
                trade["quantity"],
                trade["gross_pnl"],
                trade["entry_fee"],
                trade["exit_fee"],
                trade["net_pnl"],
                trade["exit_reason"],
                trade["balance"]
            ))

        conn.execute("""
            UPDATE bot_state
            SET
                balance = ?,
                position_json = ?,
                last_processed_open_time = ?
            WHERE id = 1
        """, (
            balance,
            position_json,
            str(last_processed_open_time)
        ))

        conn.commit()


def get_trade_history():

    initialize_database()

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT *
            FROM trades
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def reset_session():

    initialize_database()

    with get_connection() as conn:

        conn.execute("DELETE FROM trades")
        conn.execute("DELETE FROM bot_state")

        conn.commit()
