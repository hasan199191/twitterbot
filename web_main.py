from flask import Flask
import threading
import time
import os
from main import run_bot  # main.py içindeki bot fonksiyonun

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def bot_runner():
    while True:
        try:
            print("Bot başlatılıyor...")
            run_bot()
        except Exception as e:
            print(f"Bot hatası: {e}")
        time.sleep(3600)  # 1 saatte bir çalıştır

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Flask sunucusu {port} portunda çalışıyor...")

    # Flask sunucusu önce çalışmalı ki Render portu görsün
    # Botu ayrı bir thread olarak başlat
    t = threading.Thread(target=bot_runner)
    t.daemon = True
    t.start()

    # Flask app'i başlat
    app.run(host="0.0.0.0", port=port)
