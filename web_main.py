from flask import Flask
import threading
import time
import os
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
        time.sleep(3600)  # Her 1 saatte bir botu tekrar çalıştır

@app.before_first_request
def activate_bot():
    t = threading.Thread(target=bot_runner)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
