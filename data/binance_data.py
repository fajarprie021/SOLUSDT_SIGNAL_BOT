import requests
import pandas as pd

# Binance USDⓈ-M Futures API
BASE_URL = "https://fapi.binance.com"


def get_market_data(
    symbol="SOLUSDT",
    interval="1m",
    limit=200
):
    """
    Mengambil data candlestick Binance Futures.
    Hanya candle yang sudah selesai digunakan.
    """

    endpoint = f"{BASE_URL}/fapi/v1/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(
        endpoint,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "trades",
        "taker_buy_volume",
        "taker_buy_quote",
        "ignore"
    ]

    df = pd.DataFrame(data, columns=columns)

    # Konversi kolom harga dan volume
    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col])

    # Konversi timestamp
    df["open_time"] = pd.to_datetime(
        df["open_time"],
        unit="ms",
        utc=True
    )

    df["close_time"] = pd.to_datetime(
        df["close_time"],
        unit="ms",
        utc=True
    )

    # Filter candle yang sudah selesai
    now = pd.Timestamp.now(tz="UTC")

    df = df[
        df["close_time"] <= now
    ].copy()

    return df.reset_index(drop=True)