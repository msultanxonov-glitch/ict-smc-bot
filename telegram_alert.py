"""Telegram botga signal xabarlarini yuborish."""
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[OGOHLANTIRISH] Telegram sozlanmagan. .env faylini to'ldiring.")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    resp = requests.post(url, json=payload, timeout=10)
    if not resp.ok:
        print(f"[XATOLIK] Telegramga yuborilmadi: {resp.text}")


def format_signal_message(symbol_name: str, analysis: dict) -> str:
    lines = [
        f"<b>📊 {symbol_name} — {analysis['signal']} signal</b>",
        f"HTF trend: {analysis['htf_trend']}",
        "",
        "<b>Sabablar:</b>",
    ]
    for r in analysis["reason"]:
        lines.append(f"• {r}")

    if analysis.get("ltf_sweep"):
        s = analysis["ltf_sweep"]
        lines.append("")
        lines.append(f"Sweep turi: {s['type']} (level: {s['level']:.2f})")

    if analysis.get("mtf_order_blocks"):
        lines.append("")
        lines.append("<b>So'nggi Order Block'lar:</b>")
        for ob in analysis["mtf_order_blocks"]:
            lines.append(f"• {ob['type']}: {ob['bottom']:.2f} - {ob['top']:.2f}")

    lines.append("")
    lines.append("⚠️ Bu avtomatik tahlil, moliyaviy maslahat emas. O'zingiz tekshiring.")
    return "\n".join(lines)
