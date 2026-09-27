"""
Bot sozlamalarini .env fayldan (yoki Render Environment Variables'dan) o'qiydi.
"""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "")

SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "1200"))

SYMBOLS = [
    {"name": "XAUUSD", "source": "twelvedata", "td_symbol": "XAU/USD"},
    {"name": "NASDAQ", "source": "twelvedata", "td_symbol": "QQQ"},
    {"name": "BTCUSD", "source": "twelvedata", "td_symbol": "BTC/USD"},
]

TIMEFRAMES = {
    "HTF": "H4",
    "MTF": "H1",
    "LTF": "M15",
}

# ============== AVTOMAT SAVDO (Binance) ==============
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BINANCE_TESTNET = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
AUTO_TRADE_ENABLED = os.getenv("AUTO_TRADE_ENABLED", "true").lower() == "true"

BINANCE_SYMBOL = "BTCUSDT"
BINANCE_RISK_PERCENT = float(os.getenv("BINANCE_RISK_PERCENT", "1.0"))
BINANCE_RISK_REWARD = float(os.getenv("BINANCE_RISK_REWARD", "1.5"))
BINANCE_MAX_DAILY_TRADES = int(os.getenv("BINANCE_MAX_DAILY_TRADES", "3"))
BINANCE_MAX_DAILY_LOSS_PERCENT = float(os.getenv("BINANCE_MAX_DAILY_LOSS_PERCENT", "5.0"))
