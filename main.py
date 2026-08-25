import os
import sys
import time
import logging
import threading
from flask import Flask
from pyrogram import Client
from pyrogram.errors import FloodWait
import config

logging.getLogger("werkzeug").setLevel(logging.ERROR)

flask_app = Flask(__name__)

@flask_app.route("/")
def health_check():
    return "Pihu AI Bot is Active and Healthy on Render!", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=config.PORT, debug=False, use_reloader=False)

bot = Client(
    "gourav_bot_session",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

if __name__ == "__main__":
    if not config.BOT_TOKEN or not config.OPENROUTER_API_KEY:
        print("ERROR: BOT_TOKEN or OPENROUTER_API_KEY is missing in Environment Variables!")
        sys.exit(1)

    web_thread = threading.Thread(target=run_flask, daemon=True)
    web_thread.start()
    print(f"HTTP Server started on port {config.PORT} for Render Health Checks.")

    print("Starting Pihu AI Bot (OpenRouter Free Engine)...")
    while True:
        try:
            bot.run()
            break
        except FloodWait as e:
            print(f"Telegram FloodWait: Sleeping for {e.value} seconds...")
            time.sleep(e.value + 5)
        except Exception as e:
            print(f"Bot execution error: {e}")
            time.sleep(10)
