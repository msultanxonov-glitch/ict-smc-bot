"""
ICT / SMC (Smart Money Concepts) tahlil funksiyalari.
Diqqat: bu usullar tabiatan diskretsion bo'lib, bu yerdagi qoidalar
ularning soddalashtirilgan algoritmik talqinidir.
"""
import pandas as pd


def find_swings(df: pd.DataFrame, left: int = 2, right: int = 2) -> pd.DataFrame:
    df = df.copy()
    df["swing_high"] = False
    df["swing_low"] = False

    for i in range(left, len(df) - right):
        window_high = df["high"].iloc[i - left:i + right + 1]
        window_low = df["low"].iloc[i - left:i + right + 1]
        if df["high"].iloc[i] == window_high.max() and (window_high == df["high"].iloc[i]).sum() == 1:
            df.at[df.index[i], "swing_high"] = True
        if df["low"].iloc[i] == window_low.min() and (window_low == df["low"].iloc[i]).sum() == 1:
            df.at[df.index[i], "swing_low"] = True
    return df


def detect_market_structure(df: pd.DataFrame) -> dict:
    swings = find_swings(df)
    highs = swings[swings["swing_high"]][["time", "high"]].reset_index(drop=True)
    lows = swings[swings["swing_low"]][["time", "low"]].reset_index(drop=True)

    if len(highs) < 2 or len(lows) < 2:
        return {"trend": "aniqlanmadi", "event": None}

    last_close = df["close"].iloc[-1]
    last_high = highs["high"].iloc[-1]
    prev_high = highs["high"].iloc[-2]
    last_low = lows["low"].iloc[-1]
    prev_low = lows["low"].iloc[-2]

    higher_highs = last_high > prev_high
    higher_lows = last_low > prev_low
    lower_lows = last_low < prev_low
    lower_highs = last_high < prev_high

    if higher_highs and higher_lows:
        trend = "bullish"
    elif lower_lows and lower_highs:
        trend = "bearish"
    else:
        trend = "aralash"

    event = None
    if last_close > last_high:
        event = "BOS_up" if trend == "bullish" else "CHoCH_up"
    elif last_close < last_low:
        event = "BOS_down" if trend == "bearish" else "CHoCH_down"

    return {"trend": trend, "event": event, "last_high": last_high, "last_low": last_low}


def detect_fvg(df: pd.DataFrame, lookback: int = 50) -> list:
    fvgs = []
    start = max(2, len(df) - lookback)
    for i in range(start, len(df)):
        c1, c3 = df.iloc[i - 2], df.iloc[i]
        if c3["low"] > c1["high"]:
            fvgs.append({"type": "bullish", "index": i, "time": df["time"].iloc[i], "top": c3["low"], "bottom": c1["high"]})
        elif c3["high"] < c1["low"]:
            fvgs.append({"type": "bearish", "index": i, "time": df["time"].iloc[i], "top": c1["low"], "bottom": c3["high"]})
    return fvgs


def detect_order_blocks(df: pd.DataFrame, lookback: int = 100) -> list:
    obs = []
    start = max(3, len(df) - lookback)
    body = (df["close"] - df["open"]).abs()
    avg_body = body.rolling(20).mean()

    for i in range(start, len(df)):
        cur_body = body.iloc[i]
        avg = avg_body.iloc[i]
        if pd.isna(avg) or avg == 0:
            continue
        is_impulsive = cur_body > avg * 1.5
        if not is_impulsive:
            continue
        bullish_impulse = df["close"].iloc[i] > df["open"].iloc[i]
        prev = df.iloc[i - 1]
        prev_bearish = prev["close"] < prev["open"]
        prev_bullish = prev["close"] > prev["open"]

        if bullish_impulse and prev_bearish:
            obs.append({"type": "bullish_ob", "index": i - 1, "time": df["time"].iloc[i - 1], "top": prev["high"], "bottom": prev["low"]})
        elif not bullish_impulse and prev_bullish:
            obs.append({"type": "bearish_ob", "index": i - 1, "time": df["time"].iloc[i - 1], "top": prev["high"], "bottom": prev["low"]})
    return obs


def detect_liquidity_sweep(df: pd.DataFrame, lookback: int = 50) -> list:
    swings = find_swings(df)
    sweeps = []
    start = max(5, len(df) - lookback)

    recent_highs = swings[swings["swing_high"]]
    recent_lows = swings[swings["swing_low"]]

    for i in range(start, len(df)):
        row = df.iloc[i]
        past_highs = recent_highs[recent_highs.index < i]
        past_lows = recent_lows[recent_lows.index < i]

        if not past_highs.empty:
            level = past_highs["high"].iloc[-1]
            if row["high"] > level and row["close"] < level:
                sweeps.append({"type": "sell_side_sweep", "time": row["time"], "level": level, "wick_high": row["high"]})
        if not past_lows.empty:
            level = past_lows["low"].iloc[-1]
            if row["low"] < level and row["close"] > level:
                sweeps.append({"type": "buy_side_sweep", "time": row["time"], "level": level, "wick_low": row["low"]})
    return sweeps


def analyze_symbol(htf_df: pd.DataFrame, mtf_df: pd.DataFrame, ltf_df: pd.DataFrame) -> dict:
    htf_structure = detect_market_structure(htf_df)
    mtf_obs = detect_order_blocks(mtf_df)
    mtf_fvgs = detect_fvg(mtf_df)
    ltf_sweeps = detect_liquidity_sweep(ltf_df)
    ltf_structure = detect_market_structure(ltf_df)

    signal = None
    reason = []

    trend = htf_structure["trend"]
    last_sweep = ltf_sweeps[-1] if ltf_sweeps else None

    if trend == "bullish" and last_sweep and last_sweep["type"] == "buy_side_sweep":
        if ltf_structure.get("event") in ("BOS_up", "CHoCH_up"):
            signal = "BUY"
            reason.append("HTF trend bullish")
            reason.append("LTF'da buy-side likvidlik supurildi")
            reason.append("LTF'da tuzilma buzilishi (BOS/CHoCH) yuqoriga")

    elif trend == "bearish" and last_sweep and last_sweep["type"] == "sell_side_sweep":
        if ltf_structure.get("event") in ("BOS_down", "CHoCH_down"):
            signal = "SELL"
            reason.append("HTF trend bearish")
            reason.append("LTF'da sell-side likvidlik supurildi")
            reason.append("LTF'da tuzilma buzilishi (BOS/CHoCH) pastga")

    last_close = ltf_df["close"].iloc[-1]

    return {
        "signal": signal,
        "reason": reason,
        "htf_trend": trend,
        "mtf_order_blocks": mtf_obs[-3:],
        "mtf_fvgs": mtf_fvgs[-3:],
        "ltf_sweep": last_sweep,
        "last_close": last_close,
        "ltf_swing_high": ltf_structure.get("last_high"),
        "ltf_swing_low": ltf_structure.get("last_low"),
    }