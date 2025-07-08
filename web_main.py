from flask import Flask
import os
import threading
import time

from main import run_bot

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def bot_runner():
    while True:
        try:
            run_bot()
        except Exception as e:
            print(f"Bot çalışırken hata: {e}")
        # Botu belli aralıklarla tekrar çalıştır (örnek 1 saat)
        time.sleep(3600)


# Render'da Flask başlatılırken botu thread olarak başlatmak için before_first_request kullan
@app.before_first_request
def start_bot_thread():
    t = threading.Thread(target=bot_runner)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Sunucu {port} portunda başlatılıyor...")
    app.run(host="0.0.0.0", port=port)