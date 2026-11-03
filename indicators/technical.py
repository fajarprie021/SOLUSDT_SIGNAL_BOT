
import pandas as pd


def calculate_indicators(
    df,
    ema_fast=9,
    ema_slow=21,
    rsi_period=14,
    macd_fast=12,
    macd_slow=26,
    macd_signal=9
):

    df = df.copy()

    if ema_fast >= ema_slow:
        raise ValueError("EMA Fast harus lebih kecil dari EMA Slow")

    # EMA
    df["ema_fast"] = df["close"].ewm(
        span=ema_fast,
        adjust=False
    ).mean()

    df["ema_slow"] = df["close"].ewm(
        span=ema_slow,
        adjust=False
    ).mean()

    # Backward-compatible columns
    df["ema_9"] = df["ema_fast"]
    df["ema_21"] = df["ema_slow"]

    # RSI
    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / rsi_period,
        min_periods=rsi_period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / rsi_period,
        min_periods=rsi_period,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))

    df["rsi"] = 100 - (100 / (1 + rs))

    df.loc[
        (avg_loss == 0) & (avg_gain > 0),
        "rsi"
    ] = 100

    df.loc[
        (avg_loss == 0) & (avg_gain == 0),
        "rsi"
    ] = 50

    # MACD
    ema_macd_fast = df["close"].ewm(
        span=macd_fast,
        adjust=False
    ).mean()

    ema_macd_slow = df["close"].ewm(
        span=macd_slow,
        adjust=False
    ).mean()

    df["macd"] = ema_macd_fast - ema_macd_slow

    df["macd_signal"] = df["macd"].ewm(
        span=macd_signal,
        adjust=False
    ).mean()

    df["macd_hist"] = (
        df["macd"] - df["macd_signal"]
    )

    return df
