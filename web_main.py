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
            print(f"Bot hatası: {e}")
        time.sleep(3600)

# Bot thread'i, modül import edildiğinde başlatılır (hem gunicorn hem python için çalışır)
if not hasattr(app, 'bot_thread_started'):
    t = threading.Thread(target=bot_runner)
    t.daemon = True
    t.start()
    app.bot_thread_started = True

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Sunucu {port} portunda başlatılıyor...")
    app.run(host="0.0.0.0", port=port)
