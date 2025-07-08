from flask import Flask
import threading
import time
import os
from main import run_bot  # Botun ana fonksiyonu

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def bot_runner():
    while True:
        try:
            run_bot()
        except Exception as e:
            print(f"Bot hatası: {e}")
        time.sleep(3600)  # İstersen bu süreyi ayarla

if __name__ == "__main__":
    # Botu ayrı bir thread olarak başlat
    t = threading.Thread(target=bot_runner)
    t.daemon = True
    t.start()

    # Flask uygulamasını başlat
    port = int(os.environ.get("PORT", 10000))
    print(f"Sunucu {port} portunda başlatılıyor...")
    app.run(host="0.0.0.0", port=port)