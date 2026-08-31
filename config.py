"""
Bot sozlamalarini .env fayldan (yoki Render Environment Variables'dan) o'qiydi.
"""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "")

# Twelve Data bepul tarifi cheklovlariga mos: 8 so'rov/daqiqa, 800 so'rov/kun.
# Har skanerlashda 3 ta symbol x 3 ta timeframe = 9 so'rov ketadi, shuning
# uchun standart oraliq 20 daqiqa (1200 soniya) qilib qo'yilgan.
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "1200"))

# Kuzatiladigan instrumentlar (barchasi Twelve Data orqali)
SYMBOLS = [
    {"name": "XAUUSD", "source": "twelvedata", "td_symbol": "XAU/USD"},
    {"name": "NASDAQ", "source": "twelvedata", "td_symbol": "NDX"},
    {"name": "BTCUSD", "source": "twelvedata", "td_symbol": "BTC/USD"},
]

# Tahlil qilinadigan timeframe'lar (ICT uslubida: yuqori TF trend, quyi TF kirish)
TIMEFRAMES = {
    "HTF": "H4",   # umumiy trend/struktura uchun
    "MTF": "H1",   # order block / FVG qidirish uchun
    "LTF": "M15",  # aniq kirish nuqtasi uchun
}
