
import pandas as pd


def calculate_crossover_signal(df):
    """
    Entry signal berdasarkan EMA125 dan SMA125.
    Hanya menggunakan candle yang sudah ditutup.
    """

    required = ["close", "open_time"]

    for col in required:
        if col not in df.columns:
            raise ValueError(f"Kolom {col} tidak ditemukan.")

    if len(df) < 126:
        return {
            "signal": "WAIT",
            "reason": "Data belum mencukupi 126 candle."
        }

    data = df.copy()

    data["close"] = pd.to_numeric(
        data["close"], errors="coerce"
    )

    data = data.dropna(subset=["close"])

    data["ema125"] = data["close"].ewm(
        span=125,
        adjust=False
    ).mean()

    data["sma125"] = data["close"].rolling(
        window=125
    ).mean()

    previous = data.iloc[-2]
    current = data.iloc[-1]

    # Bullish crossover
    bullish_cross = (
        previous["ema125"] <= previous["sma125"]
        and current["ema125"] > current["sma125"]
    )

    # Bearish crossover
    bearish_cross = (
        previous["ema125"] >= previous["sma125"]
        and current["ema125"] < current["sma125"]
    )

    if bullish_cross:
        signal = "LONG"
        reason = "EMA125 crossed above SMA125"

    elif bearish_cross:
        signal = "SHORT"
        reason = "EMA125 crossed below SMA125"

    else:
        signal = "WAIT"
        reason = "No EMA125/SMA125 crossover"

    return {
        "signal": signal,
        "reason": reason,
        "ema125": float(current["ema125"]),
        "sma125": float(current["sma125"]),
        "previous_ema125": float(previous["ema125"]),
        "previous_sma125": float(previous["sma125"])
    }
