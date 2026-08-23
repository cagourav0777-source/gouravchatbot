import threading
from flask import Flask
from pyrogram import Client
import config

# --- Flask Keep-Alive Server ---
flask_app = Flask(__name__)

@flask_app.route("/")
def health():
    return "Gourav AI Bot is Active & Running!", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=config.PORT)

# --- Pyrogram Client ---
bot = Client(
    "gourav_bot_session",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

if __name__ == "__main__":
    # Background Flask thread for Koyeb / Render / Railway
    server_thread = threading.Thread(target=run_flask, daemon=True)
    server_thread.start()
    
    print("Starting Gourav AI Bot...")
    bot.run()
