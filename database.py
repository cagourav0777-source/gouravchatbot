import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client[config.DB_NAME]

chats_collection = db["chats"]
triggers_collection = db["triggers"]
history_collection = db["history"]
economy_collection = db["economy"]

# --- Chat Settings ---
async def get_chat_settings(chat_id: int) -> dict:
    try:
        chat = await chats_collection.find_one({"chat_id": chat_id})
        if not chat:
            default_settings = {
                "chat_id": chat_id,
                "is_enabled": True,
                "personality": "flirty_friendly",
            }
            await chats_collection.insert_one(default_settings)
            return default_settings
        return chat
    except Exception as e:
        print(f"DB Error: {e}")
        return {"chat_id": chat_id, "is_enabled": True, "personality": "flirty_friendly"}

async def update_chat_settings(chat_id: int, updates: dict):
    try:
        await chats_collection.update_one({"chat_id": chat_id}, {"$set": updates}, upsert=True)
    except Exception as e:
        print(f"DB Error: {e}")

# --- Triggers ---
async def add_trigger(chat_id: int, trigger: str, response: str, added_by: int):
    try:
        await triggers_collection.update_one(
            {"chat_id": chat_id, "trigger": trigger.lower().strip()},
            {"$set": {"response": response, "added_by": added_by}},
            upsert=True
        )
    except Exception as e:
        print(f"DB Error: {e}")

async def get_trigger(chat_id: int, trigger: str):
    try:
        return await triggers_collection.find_one({"chat_id": chat_id, "trigger": trigger.lower().strip()})
    except Exception as e:
        return None

async def remove_trigger(chat_id: int, trigger: str) -> bool:
    try:
        res = await triggers_collection.delete_one({"chat_id": chat_id, "trigger": trigger.lower().strip()})
        return res.deleted_count > 0
    except Exception as e:
        return False

async def list_triggers(chat_id: int):
    try:
        cursor = triggers_collection.find({"chat_id": chat_id}).limit(50)
        return await cursor.to_list(length=50)
    except Exception as e:
        return []

# --- History ---
async def get_chat_history(chat_id: int, limit: int = 6) -> list:
    try:
        doc = await history_collection.find_one({"chat_id": chat_id})
        if not doc or "messages" not in doc:
            return []
        return doc["messages"][-limit:]
    except Exception as e:
        return []

async def append_chat_history(chat_id: int, user_text: str, bot_text: str):
    try:
        await history_collection.update_one(
            {"chat_id": chat_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "parts": [{"text": user_text}]},
                            {"role": "model", "parts": [{"text": bot_text}]}
                        ],
                        "$slice": -10
                    }
                }
            },
            upsert=True
        )
    except Exception as e:
        print(f"History Append Error: {e}")

async def clear_chat_history(chat_id: int):
    try:
        await history_collection.delete_one({"chat_id": chat_id})
    except Exception as e:
        print(f"History Clear Error: {e}")

# ==============================================================================
#                        ECONOMY & RPG SYSTEM DATABASE
# ==============================================================================

async def get_user_eco(user_id: int, name: str = "Player") -> dict:
    user = await economy_collection.find_one({"user_id": user_id})
    if not user:
        new_user = {
            "user_id": user_id,
            "name": name,
            "balance": 1000,
            "xp": 0,
            "is_dead": False,
            "protection_until": None,
            "last_daily": None,
            "last_rob": None,
            "last_kill": None,
            "kills": 0,
            "robs": 0,
            "deaths": 0
        }
        await economy_collection.insert_one(new_user)
        return new_user
    # Update name if changed
    if user.get("name") != name:
        await economy_collection.update_one({"user_id": user_id}, {"$set": {"name": name}})
    return user

async def update_user_eco(user_id: int, updates: dict):
    await economy_collection.update_one({"user_id": user_id}, updates, upsert=True)

async def get_top_richest(limit: int = 10):
    cursor = economy_collection.find().sort("balance", -1).limit(limit)
    return await cursor.to_list(length=limit)

async def get_top_killers(limit: int = 10):
    cursor = economy_collection.find().sort("kills", -1).limit(limit)
    return await cursor.to_list(length=limit)
