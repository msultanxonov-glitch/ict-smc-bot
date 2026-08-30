"""
Narx (OHLC) ma'lumotlarini olib keladigan modul.
- XAUUSD, NASDAQ kabi instrumentlar -> Yahoo Finance orqali (internet, hamma joyda ishlaydi)
- BTCUSD -> Binance ochiq API orqali (kalit shart emas)
"""
import pandas as pd
import requests
import yfinance as yf

YF_INTERVAL_MAP = {
    "M15": "15m", "M30": "30m", "H1": "60m", "D1": "1d",
}
# yfinance'da to'g'ridan-to'g'ri H4 yo'q - H1'dan yig'ib (resample) hosil qilamiz
YF_PERIOD_MAP = {
    "15m": "60d", "30m": "60d", "60m": "730d", "1d": "730d",
}


def get_yfinance_candles(symbol: str, timeframe: str, count: int = 300) -> pd.DataFrame:
    """Yahoo Finance'dan OHLC ma'lumot oladi. H4 so'ralsa, H1'dan yig'ib chiqaradi."""
    if timeframe == "H4":
        base = get_yfinance_candles(symbol, "H1", count=count * 4 + 50)
        base = base.set_index("time")
        agg = base.resample("4h").agg({
            "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
        }).dropna().reset_index()
        return agg.tail(count).reset_index(drop=True)

    interval = YF_INTERVAL_MAP.get(timeframe)
    if interval is None:
        raise ValueError(f"Noma'lum timeframe: {timeframe}")
    period = YF_PERIOD_MAP[interval]

    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        raise RuntimeError(f"{symbol} uchun ma'lumot topilmadi (Yahoo Finance).")

    df = df.reset_index()
    time_col = "Datetime" if "Datetime" in df.columns else "Date"
    df = df.rename(columns={
        time_col: "time", "Open": "open", "High": "high",
        "Low": "low", "Close": "close", "Volume": "volume",
    })
    df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(None)
    return df[["time", "open", "high", "low", "close", "volume"]].tail(count).reset_index(drop=True)


BINANCE_TF_MAP = {
    "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
    "H1": "1h", "H4": "4h", "D1": "1d",
}


def get_binance_candles(symbol: str, timeframe: str, count: int = 300) -> pd.DataFrame:
    """Binance ochiq API'dan OHLC ma'lumot oladi (kalit shart emas)."""
    interval = BINANCE_TF_MAP.get(timeframe)
    if interval is None:
        raise ValueError(f"Noma'lum timeframe: {timeframe}")
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": count}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    raw = resp.json()
    df = pd.DataFrame(raw, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_vol", "trades", "taker_base", "taker_quote", "ignore"
    ])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df[["time", "open", "high", "low", "close", "volume"]]


def get_candles(symbol_config: dict, timeframe: str, count: int = 300) -> pd.DataFrame:
    """Symbol konfiguratsiyasiga qarab to'g'ri manbadan ma'lumot oladi."""
    if symbol_config["source"] == "yfinance":
        return get_yfinance_candles(symbol_config["yf_symbol"], timeframe, count)
    elif symbol_config["source"] == "binance":
        return get_binance_candles(symbol_config["binance_symbol"], timeframe, count)
    else:
        raise ValueError(f"Noma'lum manba: {symbol_config['source']}")

