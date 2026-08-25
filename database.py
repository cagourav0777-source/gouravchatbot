from motor.motor_asyncio import AsyncIOMotorClient
import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client[config.DB_NAME]

chats_collection = db["chats"]
triggers_collection = db["triggers"]
history_collection = db["history"]

# --- Chat Settings ---
async def get_chat_settings(chat_id: int) -> dict:
    chat = await chats_collection.find_one({"chat_id": chat_id})
    if not chat:
        default_settings = {
            "chat_id": chat_id,
            "is_enabled": True,
            "personality": "baka",  # Options: baka, roast, friendly
        }
        await chats_collection.insert_one(default_settings)
        return default_settings
    return chat

async def update_chat_settings(chat_id: int, updates: dict):
    await chats_collection.update_one(
        {"chat_id": chat_id},
        {"$set": updates},
        upsert=True
    )

# --- Custom Triggers (/teach) ---
async def add_trigger(chat_id: int, trigger: str, response: str, added_by: int):
    await triggers_collection.update_one(
        {"chat_id": chat_id, "trigger": trigger.lower().strip()},
        {"$set": {"response": response, "added_by": added_by}},
        upsert=True
    )

async def get_trigger(chat_id: int, trigger: str):
    return await triggers_collection.find_one({
        "chat_id": chat_id,
        "trigger": trigger.lower().strip()
    })

async def remove_trigger(chat_id: int, trigger: str) -> bool:
    res = await triggers_collection.delete_one({
        "chat_id": chat_id,
        "trigger": trigger.lower().strip()
    })
    return res.deleted_count > 0

async def list_triggers(chat_id: int):
    cursor = triggers_collection.find({"chat_id": chat_id}).limit(50)
    return await cursor.to_list(length=50)

# --- Conversation Memory ---
async def get_chat_history(chat_id: int, limit: int = 6) -> list:
    doc = await history_collection.find_one({"chat_id": chat_id})
    if not doc or "messages" not in doc:
        return []
    return doc["messages"][-limit:]

async def append_chat_history(chat_id: int, user_text: str, bot_text: str):
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

async def clear_chat_history(chat_id: int):
    await history_collection.delete_one({"chat_id": chat_id})
