import requests
import pandas as pd
from datetime import datetime, timezone

# Konfigurasi Binance Futures
BASE_URL = "https://fapi.binance.com"
SYMBOL = "SOLUSDT"
INTERVAL = "1m"
LIMIT = 100

def get_market_data():
    endpoint = f"{BASE_URL}/fapi/v1/klines"

    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "limit": LIMIT
    }

    try:
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

        # Konversi data numerik
        numeric_columns = [
            "open", "high", "low",
            "close", "volume"
        ]

        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])

        # Konversi waktu
        df["open_time"] = pd.to_datetime(
            df["open_time"], unit="ms", utc=True
        )

        df["close_time"] = pd.to_datetime(
            df["close_time"], unit="ms", utc=True
        )

        # Hanya gunakan candle yang sudah selesai
        now = pd.Timestamp.now(tz="UTC")
        df = df[df["close_time"] <= now].copy()

        print("=" * 55)
        print("BINANCE FUTURES CONNECTION TEST")
        print("=" * 55)

        print(f"Symbol       : {SYMBOL}")
        print(f"Timeframe    : {INTERVAL}")
        print(f"Data candles : {len(df)}")

        print("\n5 CANDLE TERAKHIR:")
        print(
            df[["open_time", "open", "high",
                "low", "close", "volume"]]
            .tail(5)
            .to_string(index=False)
        )

        print("\nHarga terakhir:", df["close"].iloc[-1])
        print("Status: CONNECTION SUCCESS")

        return df

    except Exception as e:
        print("CONNECTION FAILED")
        print("Error:", str(e))
        return None


if __name__ == "__main__":
    get_market_data()