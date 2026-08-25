import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URI = os.environ.get("MONGO_URI", "")
DB_NAME = os.environ.get("DB_NAME", "gourav_ai_db")

# GitHub Official Free Token
GITHUB_TOKEN = (
    os.environ.get("GITHUB_TOKEN") or 
    os.environ.get("OPENROUTER_API_KEY") or 
    os.environ.get("OPENAI_API_KEY") or 
    ""
)

PORT = int(os.environ.get("PORT", 10000))
