"""
Render.com (va shunga o'xshash bepul platformalar) uchun kichik web-server.
Bepul tariflar odatda faqat "web service"ni tirik saqlaydi, shuning uchun
signal skanerlash tsiklini orqa fon oqimida (background thread) ishga
tushiramiz, tashqaridan esa oddiy HTTP endpoint ko'rinadi.
"""
import os
import threading
from flask import Flask

from main import scan_loop

app = Flask(__name__)
_started = False
_lock = threading.Lock()


@app.route("/")
def health():
    return "ICT/SMC signal bot ishlayapti ✅"


def _start_background_once():
    global _started
    with _lock:
        if not _started:
            thread = threading.Thread(target=scan_loop, daemon=True)
            thread.start()
            _started = True


_start_background_once()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
