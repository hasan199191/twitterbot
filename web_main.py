from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello Render!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)