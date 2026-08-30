"""
Asosiy skanerlash tsikli:
Har SCAN_INTERVAL_SECONDS oralig'ida barcha SYMBOLS bo'yicha
HTF/MTF/LTF ma'lumot olinadi, ICT/SMC tahlil qilinadi va
yangi signal topilsa Telegramga yuboriladi.
"""
import time
import traceback

from config import SYMBOLS, TIMEFRAMES, SCAN_INTERVAL_SECONDS
from data_feed import get_candles
from smc_ict import analyze_symbol
from telegram_alert import send_telegram_message, format_signal_message

# Har bir symbol uchun oxirgi yuborilgan signalni saqlab, takroriy xabar yubormaslik uchun
_last_signal_state = {}


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
                message = format_signal_message(name, analysis)
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
    """Cheksiz tsiklda skanerlaydi. Bulut serverda fon jarayon sifatida ishga tushiriladi."""
    print("ICT/SMC signal bot ishga tushdi.")
    send_telegram_message("🤖 ICT/SMC signal bot ishga tushdi. Kuzatilayotgan instrumentlar: "
                           + ", ".join(s["name"] for s in SYMBOLS))
    while True:
        scan_once()
        time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    scan_loop()
