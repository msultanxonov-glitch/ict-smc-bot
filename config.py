"""
Bot sozlamalarini .env fayldan o'qiydi.
Ishga tushirishdan oldin .env.example faylini .env deb nomlang
va o'z ma'lumotlaringizni kiriting.
"""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "60"))

# Kuzatiladigan instrumentlar va ularning manba turi
# "yfinance" -> Yahoo Finance (internet orqali, telefon/Termux'da ham ishlaydi)
# "binance" -> Binance ochiq API orqali
SYMBOLS = [
    {"name": "XAUUSD", "source": "yfinance", "yf_symbol": "GC=F"},   # Gold futures
    {"name": "NASDAQ", "source": "yfinance", "yf_symbol": "NQ=F"},   # Nasdaq-100 futures
    {"name": "BTCUSD", "source": "yfinance", "yf_symbol": "BTC-USD"},

]

# Tahlil qilinadigan timeframe'lar (ICT uslubida: yuqori TF trend, quyi TF kirish)
TIMEFRAMES = {
    "HTF": "H4",   # umumiy trend/struktura uchun
    "MTF": "H1",   # order block / FVG qidirish uchun
    "LTF": "M15",  # aniq kirish nuqtasi uchun
}
