from flask import Flask
import threading
import time
from main import run_bot

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

@app.route("/healthz")
def healthz():
    return "ok"

def bot_runner():
    while True:
        try:
            run_bot()
        except Exception as e:
            print(f"Bot run failed with error: {e}")
        # Her saat başı tekrar başlatmak için 3600 saniye bekle
        time.sleep(3600)


# Botu Flask başlatıldıktan sonra thread ile başlatmak için before_first_request kullan
@app.before_first_request
def activate_bot():
    t = threading.Thread(target=bot_runner)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
