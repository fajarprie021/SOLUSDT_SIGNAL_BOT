
import pandas as pd

from datetime import datetime, timezone
from data.binance_data import get_market_data


# ==========================================
# MULTI TIMEFRAME CONFIGURATION
# ==========================================

SYMBOL = "SOLUSDT"

TIMEFRAMES = {
    "4h": {
        "interval": "4h",
        "seconds": 4 * 60 * 60,
        "limit": 300
    },
    "1h": {
        "interval": "1h",
        "seconds": 60 * 60,
        "limit": 300
    },
    "15m": {
        "interval": "15m",
        "seconds": 15 * 60,
        "limit": 300
    }
}


# ==========================================
# REMOVE INCOMPLETE CANDLE
# ==========================================

def remove_incomplete_candles(df, timeframe_seconds):

    df = df.copy()

    if "open_time" not in df.columns:
        raise ValueError(
            "Kolom open_time tidak ditemukan."
        )

    df["open_time"] = pd.to_datetime(
        df["open_time"],
        utc=True
    )

    current_time = pd.Timestamp.now(tz="UTC")

    candle_close_time = (
        df["open_time"]
        + pd.to_timedelta(timeframe_seconds, unit="s")
    )

    # Hanya candle yang sudah selesai
    df = df[candle_close_time <= current_time]

    return df.reset_index(drop=True)


# ==========================================
# GET SINGLE TIMEFRAME DATA
# ==========================================

def get_timeframe_data(
    symbol,
    timeframe,
    limit=300
):

    if timeframe not in TIMEFRAMES:
        raise ValueError(
            f"Timeframe tidak didukung: {timeframe}"
        )

    config = TIMEFRAMES[timeframe]

    df = get_market_data(
        symbol=symbol,
        interval=config["interval"],
        limit=limit
    )

    if df is None or df.empty:
        raise ValueError(
            f"Data {timeframe} tidak tersedia."
        )

    required_columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    for column in required_columns:

        if column not in df.columns:
            raise ValueError(
                f"Kolom {column} tidak tersedia pada {timeframe}."
            )

    # Pastikan data numerik
    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(
        subset=["open", "high", "low", "close", "volume"]
    )

    # Hapus candle yang masih berjalan
    df = remove_incomplete_candles(
        df,
        config["seconds"]
    )

    if len(df) < 200:
        raise ValueError(
            f"Data candle {timeframe} hanya {len(df)}. "
            "Minimal 200 candle tertutup diperlukan."
        )

    return df


# ==========================================
# GET ALL MULTI TIMEFRAME DATA
# ==========================================

def get_multi_timeframe_data(
    symbol=SYMBOL,
    limit=300
):

    results = {}

    for timeframe in ["4h", "1h", "15m"]:

        print(
            f"Mengambil data {symbol} timeframe {timeframe}..."
        )

        df = get_timeframe_data(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit
        )

        results[timeframe] = df

        print(
            f"Berhasil: {len(df)} candle tertutup"
        )

    return results


# ==========================================
# DISPLAY DATA INFORMATION
# ==========================================

def display_multi_timeframe_data(data):

    print("\n")
    print("=" * 65)
    print("SOLUSDT MULTI-TIMEFRAME MARKET DATA")
    print("=" * 65)

    for timeframe, df in data.items():

        print(f"\nTIMEFRAME : {timeframe}")

        print(f"Total Candle : {len(df)}")

        print(
            "Last Candle :",
            df.iloc[-1]["open_time"]
        )

        print(
            "Last Close  :",
            df.iloc[-1]["close"]
        )

    print("\n")
    print(
        "Checked at:",
        datetime.now(timezone.utc)
    )

    print("=" * 65)
