import os
import sys
import logging
import threading
from flask import Flask
from pyrogram import Client
import config

# Flask logs minimize karein
logging.getLogger("werkzeug").setLevel(logging.ERROR)

flask_app = Flask(__name__)

@flask_app.route("/")
def health_check():
    return "Gourav AI Bot is Active and Healthy on Render!", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=config.PORT, debug=False, use_reloader=False)

# --- Pyrogram Client ---
bot = Client(
    "gourav_bot_session",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

if __name__ == "__main__":
    # Check required environment variables
    if not config.BOT_TOKEN or not config.GROQ_API_KEY:
        print("ERROR: BOT_TOKEN or GROQ_API_KEY is missing in Environment Variables!")
        sys.exit(1)

    # 1. Flask Health Server start karein
    web_thread = threading.Thread(target=run_flask, daemon=True)
    web_thread.start()
    print(f"HTTP Server started on port {config.PORT} for Render Health Checks.")

    # 2. Pyrogram Bot run karein
    print("Starting Gourav AI Bot...")
    bot.run()
