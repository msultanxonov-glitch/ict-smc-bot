"""
Asosiy skanerlash tsikli:
- Har SCAN_INTERVAL_SECONDS oralig'ida barcha SYMBOLS bo'yicha tahlil qilinadi.
- XAUUSD/NASDAQ uchun - faqat Telegram signal.
- BTCUSD uchun - agar AUTO_TRADE_ENABLED bo'lsa va signal BUY bo'lsa,
  Binance'da (testnet yoki live) avtomatik order ochiladi.
"""
import time
import traceback
from datetime import datetime, timezone

from config import (
    SYMBOLS, TIMEFRAMES, SCAN_INTERVAL_SECONDS, AUTO_TRADE_ENABLED,
    BINANCE_MAX_DAILY_TRADES, BINANCE_MAX_DAILY_LOSS_PERCENT,
)
from data_feed import get_candles
from smc_ict import analyze_symbol
from telegram_alert import send_telegram_message, format_signal_message

_last_signal_state = {}

# Binance kunlik limitlar uchun holat
_daily_trade_count = 0
_daily_start_balance = None
_current_day = None


def _reset_daily_state():
    global _daily_trade_count, _daily_start_balance, _current_day
    _daily_trade_count = 0
    _current_day = datetime.now(timezone.utc).date()
    try:
        import binance_trade
        _daily_start_balance = binance_trade.get_account_balance("USDT")
    except Exception as e:
        print(f"[XATOLIK] Binance balansini olishda xato: {e}")
        _daily_start_balance = None


def _check_new_day():
    today = datetime.now(timezone.utc).date()
    if _current_day != today:
        _reset_daily_state()


def _daily_limits_ok() -> bool:
    """Kunlik savdolar soni va zarar limitini tekshiradi."""
    if _daily_trade_count >= BINANCE_MAX_DAILY_TRADES:
        print("[INFO] Kunlik maksimal savdolar soniga yetildi, bugun avtomat savdo to'xtatildi.")
        return False

    if _daily_start_balance:
        try:
            import binance_trade
            current_balance = binance_trade.get_account_balance("USDT")
            loss_pct = (_daily_start_balance - current_balance) / _daily_start_balance * 100.0
            if loss_pct >= BINANCE_MAX_DAILY_LOSS_PERCENT:
                print("[INFO] Kunlik zarar limitiga yetildi, bugun avtomat savdo to'xtatildi.")
                return False
        except Exception as e:
            print(f"[XATOLIK] Kunlik zararni tekshirishda xato: {e}")

    return True


def try_auto_trade_btc(analysis: dict):
    """BTCUSD uchun avtomat savdo urinishi. Faqat BUY signalida ishlaydi (spot cheklovi)."""
    global _daily_trade_count

    if not AUTO_TRADE_ENABLED:
        return None
    if analysis["signal"] != "BUY":
        return None

    _check_new_day()
    if not _daily_limits_ok():
        return {"success": False, "reason": "Kunlik limit (savdolar soni yoki zarar) ga yetildi."}

    try:
        import binance_trade
        if binance_trade.has_open_position():
            return {"success": False, "reason": "Allaqachon ochiq BTC pozitsiya bor."}

        entry_price = analysis["last_close"]
        sl_price = analysis.get("ltf_swing_low")
        if analysis.get("ltf_sweep"):
            sl_price = min(sl_price or entry_price, analysis["ltf_sweep"].get("wick_low", entry_price))

        if not sl_price or sl_price >= entry_price:
            return {"success": False, "reason": "SL narxi hisoblanmadi."}

        result = binance_trade.execute_buy_trade(entry_price, sl_price)
        if result.get("success"):
            _daily_trade_count += 1
        return result

    except Exception as e:
        traceback.print_exc()
        return {"success": False, "reason": f"Xato: {e}"}


def scan_once():
    for sym in SYMBOLS:
        name = sym["name"]
        try:
            htf_df = get_candles(sym, TIMEFRAMES["HTF"], count=200)
            mtf_df = get_candles(sym, TIMEFRAMES["MTF"], count=200)
            ltf_df = get_candles(sym, TIMEFRAMES["LTF"], count=200)

            analysis = analyze_symbol(htf_df, mtf_df, ltf_df)
            signal = analysis["signal"]

            if signal and _last_signal_state.get(name) != signal:
                auto_trade_result = None
                if name == "BTCUSD":
                    auto_trade_result = try_auto_trade_btc(analysis)

                message = format_signal_message(name, analysis, auto_trade_result)
                send_telegram_message(message)
                print(f"[SIGNAL] {name}: {signal}")
                _last_signal_state[name] = signal
            elif not signal:
                _last_signal_state[name] = None
            else:
                print(f"[...] {name}: signal o'zgarmadi ({signal})")

        except Exception as e:
            print(f"[XATOLIK] {name}: {e}")
            traceback.print_exc()


def scan_loop():
    print("ICT/SMC signal bot ishga tushdi.")
    _reset_daily_state()

    mode = "AVTOMAT SAVDO YOQILGAN (BTCUSD)" if AUTO_TRADE_ENABLED else "faqat signal"
    send_telegram_message(
        "🤖 ICT/SMC bot ishga tushdi. Kuzatilayotgan instrumentlar: "
        + ", ".join(s["name"] for s in SYMBOLS)
        + f"\nRejim: {mode}"
    )
    while True:
        scan_once()
        time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    scan_loop()
