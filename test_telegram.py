"""
Telegram bot ulanishini tekshirish uchun oddiy skript.
Ishlatish: python test_telegram.py
.env faylida TELEGRAM_BOT_TOKEN va TELEGRAM_CHAT_ID to'ldirilgan bo'lishi kerak.
"""
from telegram_alert import send_telegram_message

if __name__ == "__main__":
    send_telegram_message("✅ Bot muvaffaqiyatli ulandi! ICT/SMC signal bot ishga tayyor.")
    print("Xabar yuborildi (yoki .env to'ldirilmagan bo'lsa, yuqorida ogohlantirish ko'rinadi).")
