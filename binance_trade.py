"""
Binance orqali avtomat savdo (spot).

Testnet (BINANCE_TESTNET=true, standart): https://testnet.binance.vision
- Soxta pul bilan ishlaydi, haqiqiy pul xavfi yo'q.
- API kalitni https://testnet.binance.vision saytida GitHub orqali kirib olasiz.

Live (BINANCE_TESTNET=false): https://api.binance.com
- HAQIQIY PUL bilan ishlaydi. Faqat testnet'da yetarlicha sinagandan
  keyin, juda kichik risk bilan yoqish tavsiya etiladi.

Cheklov: spot hisobda haqiqiy "shortlash" (SELL signalida) mumkin emas,
shuning uchun bu modul faqat BUY (long) signallarini avtomatik bajaradi.
SELL signali kelsa, faqat Telegramga xabar beriladi, order ochilmaydi.
"""
import time
import hmac
import hashlib
import math
from urllib.parse import urlencode

import requests

from config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, BINANCE_TESTNET, BINANCE_SYMBOL,
    BINANCE_RISK_PERCENT, BINANCE_RISK_REWARD,
)

BASE_URL = "https://testnet.binance.vision" if BINANCE_TESTNET else "https://api.binance.com"

_symbol_filters_cache = {}


def _signed_request(method: str, path: str, params: dict) -> dict:
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        raise RuntimeError("BINANCE_API_KEY / BINANCE_API_SECRET sozlanmagan.")

    params = dict(params)
    params["timestamp"] = int(time.time() * 1000)
    params["recvWindow"] = 10000
    query = urlencode(params)
    signature = hmac.new(BINANCE_API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    query += f"&signature={signature}"

    url = f"{BASE_URL}{path}?{query}"
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}

    resp = requests.request(method, url, headers=headers, timeout=15)
    if not resp.ok:
        raise RuntimeError(f"Binance API xatosi ({resp.status_code}): {resp.text}")
    return resp.json()


def get_account_balance(asset: str = "USDT") -> float:
    data = _signed_request("GET", "/api/v3/account", {})
    for bal in data.get("balances", []):
        if bal["asset"] == asset:
            return float(bal["free"])
    return 0.0


def get_symbol_filters(symbol: str = BINANCE_SYMBOL) -> dict:
    if symbol in _symbol_filters_cache:
        return _symbol_filters_cache[symbol]

    resp = requests.get(f"{BASE_URL}/api/v3/exchangeInfo", params={"symbol": symbol}, timeout=15)
    resp.raise_for_status()
    info = resp.json()["symbols"][0]

    filters = {}
    for f in info["filters"]:
        if f["filterType"] == "LOT_SIZE":
            filters["stepSize"] = float(f["stepSize"])
            filters["minQty"] = float(f["minQty"])
        elif f["filterType"] == "PRICE_FILTER":
            filters["tickSize"] = float(f["tickSize"])
        elif f["filterType"] in ("MIN_NOTIONAL", "NOTIONAL"):
            filters["minNotional"] = float(f.get("minNotional", f.get("minNotionalValue", 5)))

    _symbol_filters_cache[symbol] = filters
    return filters


def _round_step(value: float, step: float) -> float:
    precision = int(round(-math.log10(step))) if step < 1 else 0
    return math.floor(value / step) * step if precision == 0 else round(math.floor(value / step) * step, precision)


def calc_position_size(entry_price: float, sl_price: float) -> float:
    """Risk foiziga asoslanib BTC miqdorini hisoblaydi."""
    balance = get_account_balance("USDT")
    risk_amount = balance * BINANCE_RISK_PERCENT / 100.0
    sl_distance = abs(entry_price - sl_price)
    if sl_distance <= 0:
        return 0.0

    quantity = risk_amount / sl_distance
    filters = get_symbol_filters()
    quantity = _round_step(quantity, filters.get("stepSize", 0.00001))

    notional = quantity * entry_price
    if notional < filters.get("minNotional", 5):
        return 0.0
    if quantity < filters.get("minQty", 0.00001):
        return 0.0
    return quantity


def has_open_position() -> bool:
    """BTC balansi minimal miqdordan ko'p bo'lsa, ochiq pozitsiya bor deb hisoblaymiz."""
    balance = get_account_balance("BTC")
    filters = get_symbol_filters()
    return balance > filters.get("minQty", 0.0001)


def place_market_buy(quantity: float) -> dict:
    filters = get_symbol_filters()
    qty_str = f"{quantity:.8f}".rstrip("0").rstrip(".")
    return _signed_request("POST", "/api/v3/order", {
        "symbol": BINANCE_SYMBOL,
        "side": "BUY",
        "type": "MARKET",
        "quantity": qty_str,
    })


def place_oco_sell(quantity: float, take_profit_price: float, stop_price: float, stop_limit_price: float) -> dict:
    """Xarid qilingandan keyin avtomatik TP/SL uchun OCO order qo'yadi."""
    filters = get_symbol_filters()
    tick = filters.get("tickSize", 0.01)

    def fmt_price(p):
        return f"{_round_step(p, tick):.8f}".rstrip("0").rstrip(".")

    qty_str = f"{quantity:.8f}".rstrip("0").rstrip(".")

    return _signed_request("POST", "/api/v3/order/oco", {
        "symbol": BINANCE_SYMBOL,
        "side": "SELL",
        "quantity": qty_str,
        "price": fmt_price(take_profit_price),
        "stopPrice": fmt_price(stop_price),
        "stopLimitPrice": fmt_price(stop_limit_price),
        "stopLimitTimeInForce": "GTC",
    })


def execute_buy_trade(entry_price: float, sl_price: float) -> dict:
    """
    To'liq kirish jarayoni: miqdorni hisoblash -> market BUY -> OCO SELL (TP/SL).
    Muvaffaqiyatli bo'lsa {"success": True, ...} qaytaradi.
    """
    quantity = calc_position_size(entry_price, sl_price)
    if quantity <= 0:
        return {"success": False, "reason": "Miqdor hisoblanmadi (balans yetarli emas yoki minNotional'dan kichik)."}

    buy_order = place_market_buy(quantity)

    sl_distance = abs(entry_price - sl_price)
    tp_price = entry_price + sl_distance * BINANCE_RISK_REWARD
    stop_limit_price = sl_price * 0.999

    try:
        oco_order = place_oco_sell(quantity, tp_price, sl_price, stop_limit_price)
    except Exception as e:
        return {
            "success": True, "quantity": quantity, "buy_order": buy_order,
            "oco_error": str(e),
            "warning": "BUY bajarildi, lekin TP/SL (OCO) qo'yilmadi - qo'lda kuzating!",
        }

    return {
        "success": True, "quantity": quantity, "entry": entry_price,
        "sl": sl_price, "tp": tp_price, "buy_order": buy_order, "oco_order": oco_order,
    }
