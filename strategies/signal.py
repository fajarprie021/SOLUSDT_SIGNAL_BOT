
def generate_signal(df, ema_fast=9, ema_slow=21):

    required_columns = [
        "ema_fast",
        "ema_slow",
        "rsi",
        "macd",
        "macd_signal",
        "macd_hist"
    ]

    if len(df) < 2:
        return {
            "signal": "WAIT",
            "reason": "Data belum mencukupi"
        }

    for column in required_columns:

        if column not in df.columns:
            return {
                "signal": "WAIT",
                "reason": f"Indikator {column} belum tersedia"
            }

    current = df.iloc[-1]

    if current[required_columns].isna().any():

        return {
            "signal": "WAIT",
            "reason": "Indikator belum siap"
        }

    # LONG CONDITIONS
    long_condition = (
        current["ema_fast"] > current["ema_slow"]
        and current["rsi"] > 50
        and current["macd"] > current["macd_signal"]
        and current["macd_hist"] > 0
    )

    # SHORT CONDITIONS
    short_condition = (
        current["ema_fast"] < current["ema_slow"]
        and current["rsi"] < 50
        and current["macd"] < current["macd_signal"]
        and current["macd_hist"] < 0
    )

    if long_condition:

        return {
            "signal": "LONG",
            "reason": (
                f"EMA {ema_fast} > EMA {ema_slow}; "
                "RSI bullish; MACD bullish"
            )
        }

    if short_condition:

        return {
            "signal": "SHORT",
            "reason": (
                f"EMA {ema_fast} < EMA {ema_slow}; "
                "RSI bearish; MACD bearish"
            )
        }

    return {
        "signal": "WAIT",
        "reason": "Belum ada konfirmasi lengkap"
    }
