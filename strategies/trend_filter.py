
import pandas as pd


def calculate_trend(df):
    """
    Menghitung tren berdasarkan:
    EMA 20, EMA 50, dan SMA 200.

    Input:
        df = DataFrame OHLCV dengan kolom close.

    Output:
        BULLISH (+1), BEARISH (-1), atau NEUTRAL (0).
    """

    required_columns = ["close"]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(
                f"Kolom {column} tidak ditemukan."
            )

    if len(df) < 200:
        return {
            "trend": "NEUTRAL",
            "score": 0,
            "reason": "Data belum mencukupi 200 candle."
        }

    data = df.copy()

    data["ema20"] = data["close"].ewm(
        span=20,
        adjust=False
    ).mean()

    data["ema50"] = data["close"].ewm(
        span=50,
        adjust=False
    ).mean()

    data["sma200"] = data["close"].rolling(
        window=200
    ).mean()

    current = data.iloc[-1]

    close = current["close"]
    ema20 = current["ema20"]
    ema50 = current["ema50"]
    sma200 = current["sma200"]

    # Bullish condition
    bullish = (
        close > ema20
        and ema20 > ema50
        and close > sma200
    )

    # Bearish condition
    bearish = (
        close < ema20
        and ema20 < ema50
        and close < sma200
    )

    if bullish:

        return {
            "trend": "BULLISH",
            "score": 1,
            "reason": "Close > EMA20 > EMA50 dan Close > SMA200",
            "close": float(close),
            "ema20": float(ema20),
            "ema50": float(ema50),
            "sma200": float(sma200)
        }

    elif bearish:

        return {
            "trend": "BEARISH",
            "score": -1,
            "reason": "Close < EMA20 < EMA50 dan Close < SMA200",
            "close": float(close),
            "ema20": float(ema20),
            "ema50": float(ema50),
            "sma200": float(sma200)
        }

    return {
        "trend": "NEUTRAL",
        "score": 0,
        "reason": "Kondisi bullish atau bearish belum terpenuhi",
        "close": float(close),
        "ema20": float(ema20),
        "ema50": float(ema50),
        "sma200": float(sma200)
    }


def calculate_multi_timeframe_trend(
    df_4h,
    df_1h,
    df_15m
):
    """
    Menggabungkan skor tren 4H, 1H, dan 15M.
    """

    trend_4h = calculate_trend(df_4h)
    trend_1h = calculate_trend(df_1h)
    trend_15m = calculate_trend(df_15m)

    total_score = (
        trend_4h["score"]
        + trend_1h["score"]
        + trend_15m["score"]
    )

    if total_score >= 2:
        final_trend = "BULLISH"

    elif total_score <= -2:
        final_trend = "BEARISH"

    else:
        final_trend = "NEUTRAL"

    return {
        "trend_4h": trend_4h,
        "trend_1h": trend_1h,
        "trend_15m": trend_15m,
        "total_score": total_score,
        "final_trend": final_trend
    }
