
import pandas as pd


def calculate_triple_ema_signal(df):
    """
    Triple EMA Crossover Strategy

    EMA 8   : Fast
    EMA 21  : Medium
    EMA 185 : Trend Filter

    LONG:
        EMA 8 crosses above EMA 21
        EMA 8 and EMA 21 are above EMA 185

    SHORT:
        EMA 8 crosses below EMA 21
        EMA 8 and EMA 21 are below EMA 185

    Input must contain CLOSED 1-minute candles.
    """

    required_columns = ["close"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(
                f"Kolom {col} tidak ditemukan."
            )

    if len(df) < 300:
        return {
            "signal": "WAIT",
            "reason": "Minimal 300 candle diperlukan untuk warm-up EMA.",
        }

    data = df.copy()

    data["close"] = pd.to_numeric(
        data["close"],
        errors="coerce"
    )

    data = data.dropna(subset=["close"])

    if len(data) < 300:
        return {
            "signal": "WAIT",
            "reason": "Data valid kurang dari 300 candle."
        }

    # ======================================
    # CALCULATE EMA
    # ======================================

    data["ema8"] = data["close"].ewm(
        span=8,
        adjust=False
    ).mean()

    data["ema21"] = data["close"].ewm(
        span=21,
        adjust=False
    ).mean()

    data["ema185"] = data["close"].ewm(
        span=185,
        adjust=False
    ).mean()

    previous = data.iloc[-2]
    current = data.iloc[-1]

    # ======================================
    # BULLISH CROSSOVER
    # ======================================

    bullish_cross = (
        previous["ema8"] <= previous["ema21"]
        and current["ema8"] > current["ema21"]
        and current["ema8"] > current["ema185"]
        and current["ema21"] > current["ema185"]
    )

    # ======================================
    # BEARISH CROSSOVER
    # ======================================

    bearish_cross = (
        previous["ema8"] >= previous["ema21"]
        and current["ema8"] < current["ema21"]
        and current["ema8"] < current["ema185"]
        and current["ema21"] < current["ema185"]
    )

    # ======================================
    # SIGNAL
    # ======================================

    if bullish_cross:

        signal = "LONG"
        reason = (
            "EMA8 crossed above EMA21 "
            "and both EMA are above EMA185."
        )

    elif bearish_cross:

        signal = "SHORT"
        reason = (
            "EMA8 crossed below EMA21 "
            "and both EMA are below EMA185."
        )

    else:

        signal = "WAIT"
        reason = "No valid triple EMA crossover."

    return {
        "signal": signal,
        "reason": reason,

        "ema8": float(current["ema8"]),
        "ema21": float(current["ema21"]),
        "ema185": float(current["ema185"]),

        "previous_ema8": float(previous["ema8"]),
        "previous_ema21": float(previous["ema21"]),

        "close": float(current["close"])
    }
