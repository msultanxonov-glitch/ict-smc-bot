"""
Narx (OHLC) ma'lumotlarini olib keladigan modul.
Manba: Twelve Data (twelvedata.com) - bepul API, bulut serverlardan
(Render kabi) ishonchli ishlaydi. Yahoo Finance va Binance bulut
IP manzillarini bloklab qo'yganligi sababli ulardan voz kechildi.

Bepul API kalitini https://twelvedata.com/ saytidan olish mumkin
(ro'yxatdan o'tish bepul, kredit karta shart emas).
"""
import pandas as pd
import requests

from config import TWELVEDATA_API_KEY

TD_INTERVAL_MAP = {
    "M15": "15min", "M30": "30min", "H1": "1h", "H4": "4h", "D1": "1day",
}


def get_twelvedata_candles(symbol: str, timeframe: str, count: int = 300) -> pd.DataFrame:
    """Twelve Data API'dan OHLC ma'lumot oladi."""
    interval = TD_INTERVAL_MAP.get(timeframe)
    if interval is None:
        raise ValueError(f"Noma'lum timeframe: {timeframe}")

    if not TWELVEDATA_API_KEY:
        raise RuntimeError(
            "TWELVEDATA_API_KEY sozlanmagan. twelvedata.com'dan bepul API "
            "kalit oling va Render Environment Variables'ga qo'shing."
        )

    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": min(count, 5000),
        "apikey": TWELVEDATA_API_KEY,
        "order": "ASC",
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") == "error" or "values" not in data:
        raise RuntimeError(f"{symbol} uchun ma'lumot topilmadi (Twelve Data): {data.get('message', data)}")

    values = data["values"]
    df = pd.DataFrame(values)
    df = df.rename(columns={"datetime": "time"})
    df["time"] = pd.to_datetime(df["time"])
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
    else:
        df["volume"] = 0.0

    df = df.sort_values("time").reset_index(drop=True)
    return df[["time", "open", "high", "low", "close", "volume"]].tail(count).reset_index(drop=True)


def get_candles(symbol_config: dict, timeframe: str, count: int = 300) -> pd.DataFrame:
    """Symbol konfiguratsiyasiga qarab ma'lumot oladi."""
    if symbol_config["source"] == "twelvedata":
        return get_twelvedata_candles(symbol_config["td_symbol"], timeframe, count)
    else:
        raise ValueError(f"Noma'lum manba: {symbol_config['source']}")
