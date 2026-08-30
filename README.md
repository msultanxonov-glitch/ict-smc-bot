# ICT / SMC Signal Bot (XAUUSD, NASDAQ, BTCUSD) — Render.com'da 24/7

Bu bot narxni kuzatib, ICT/SMC uslubidagi belgilarni (Market Structure /
BOS-CHoCH, Order Block, Fair Value Gap, Liquidity Sweep) avtomatik
aniqlaydi va topilgan signalni Telegram botga yuboradi. Render.com'ning
bepul tarifida 24/7 ishlaydigan qilib sozlangan.

## ⚠️ Muhim ogohlantirish

- Bu **signal beruvchi yordamchi**, "kafolatli foyda beruvchi robot" emas.
- ICT/SMC — diskretsion (odam qarori kerak bo'ladigan) tahlil uslubi. Bu
  yerdagi qoidalar soddalashtirilgan algoritmik talqin, 100% aniq emas.
- Hozircha bot **faqat signal yuboradi**, order avtomatik ochilmaydi.
- Hech qanday dastur bozor harakatini kafolatlab bera olmaydi.

## 1-qadam: Telegram bot ma'lumotlarini tayyorlang

Sizda allaqachon bot bor — shundan:
- **Token**: @BotFather'dan olgan token.
- **chat_id**: @userinfobot'ga yozib oling.

## 2-qadam: Kodni GitHub'ga yuklang

1. github.com'da bepul akkaunt oching (agar yo'q bo'lsa).
2. Yangi **private repository** yarating (masalan `ict-smc-bot`).
3. Shu papkadagi barcha fayllarni o'sha repoga yuklang (GitHub sayti orqali
   "Add file → Upload files" qilib, zip'ni yozib, fayllarni tortib
   tashlash ham bo'ladi — kompyuter yoki telefon brauzeridan ham mumkin).

## 3-qadam: Render.com'da joylashtirish

1. render.com'da bepul akkaunt oching (GitHub bilan kirish qulay).
2. **New → Web Service** tugmasini bosing.
3. GitHub repongizni tanlang.
4. Sozlamalar:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 1 --timeout 120 app:app`
   - **Instance Type**: Free
5. **Environment Variables** bo'limida qo'shing (`.env` fayl o'rniga):
   - `TELEGRAM_BOT_TOKEN` = sizning tokeningiz
   - `TELEGRAM_CHAT_ID` = sizning chat_id'ingiz
   - `SCAN_INTERVAL_SECONDS` = `60`
6. **Create Web Service** tugmasini bosing — Render avtomatik build qilib,
   ishga tushiradi (2-3 daqiqa vaqt oladi).

Deploy tugagach, Render sizga bir link beradi (masalan
`https://ict-smc-bot.onrender.com`). Shu link ochilsa "ICT/SMC signal bot
ishlayapti ✅" deb chiqsa — hammasi ishlayapti degani. Bir necha soniyadan
so'ng Telegram botingizga "🤖 Bot ishga tushdi" xabari kelishi kerak.

## 4-qadam: Botni "uxlab qolishdan" saqlash (muhim!)

Render'ning bepul tarifi 15 daqiqa HTTP so'rov kelmasa, servisni
"uxlatib" qo'yadi. Buni oldini olish uchun **bepul monitoring xizmati**
ishlatamiz:

1. **UptimeRobot.com**'da bepul akkaunt oching.
2. **Add New Monitor** → Monitor Type: `HTTP(s)`.
3. URL sifatida Render bergan linkni kiriting.
4. Monitoring Interval: **5 daqiqa**.
5. Saqlang.

Endi UptimeRobot har 5 daqiqada botingizni "uyg'otib" turadi va u
haqiqiy 24/7 ishlaydi.

## Qanday ishlaydi (qisqacha mantiq)

1. **HTF (H4)** — umumiy trend yo'nalishini (bullish/bearish) aniqlaydi.
2. **MTF (H1)** — Order Block va Fair Value Gap zonalarini topadi.
3. **LTF (M15)** — Liquidity Sweep ("bank manipulyatsiyasi" / stop-hunt)
   va BOS/CHoCH orqali aniq kirish trigerini qidiradi.
4. Uchala shart mos kelsa — BUY yoki SELL signal Telegramga yuboriladi.

## Narx manbalari

- **XAUUSD, NASDAQ** — Yahoo Finance (bepul, kalit shart emas).
- **BTCUSD** — Binance ochiq API (bepul, kalit shart emas).

## Mahalliy kompyuterda sinab ko'rish (ixtiyoriy)

```bash
pip install -r requirements.txt
cp .env.example .env   # va to'ldiring
python test_telegram.py   # ulanishni tekshirish
python main.py             # to'g'ridan-to'g'ri konsolda ishga tushirish
```

## Keyingi qadamlar (xohlasangiz qo'shib beraman)

- **Avtomatik order ochish**: Binance uchun `python-binance`, forex/gold
  uchun broker API (masalan cTrader, OANDA) orqali haqiqiy savdo.
- **Risk-menejment**: lot hajmini balansga qarab hisoblash, SL/TP.
- **Backtest**: strategiyani tarixiy ma'lumotda sinab statistika chiqarish.
- **Telegram buyruqlari**: `/status`, `/pause`, `/resume`.
