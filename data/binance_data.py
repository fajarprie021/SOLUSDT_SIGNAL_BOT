import requests
import pandas as pd

# Binance endpoints. Some hosting regions receive HTTP 451 from the
# Futures endpoint, so the public market-data mirror is used as a fallback.
ENDPOINTS = (
    ("Binance Futures", "https://fapi.binance.com/fapi/v1/klines"),
    ("Binance Public Data", "https://data-api.binance.vision/api/v3/klines"),
)


def get_market_data(
    symbol="SOLUSDT",
    interval="1m",
    limit=200
):
    """
    Mengambil data candlestick Binance Futures.
    Hanya candle yang sudah selesai digunakan.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    data = None
    errors = []

    for endpoint_name, endpoint in ENDPOINTS:
        try:
            response = requests.get(
                endpoint,
                params=params,
                headers={"User-Agent": "SOLUSDT-Signal-Bot/1.0"},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            break
        except requests.RequestException as exc:
            errors.append(f"{endpoint_name}: {exc}")

    if data is None:
        raise requests.RequestException(
            "Semua endpoint market data Binance gagal. "
            + " | ".join(errors)
        )

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