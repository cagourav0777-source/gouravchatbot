from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.enums import ChatType
import database as db
from gemini_client import generate_gemini_reply

@Client.on_message(filters.command(["clear", "reset"]))
async def clear_history_handler(client: Client, message: Message):
    await db.clear_chat_history(message.chat.id)
    await message.reply_text("heyy! purani chat clear ho gayi, ab batao kya chal raha hai? 🙈✨")

@Client.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text("hiii! kya chal raha hai? kaisa gaya aaj ka din? ✨")

async def should_reply(client: Client, message: Message) -> bool:
    if not message.text or message.text.startswith("/"):
        return False
    
    if message.chat.type == ChatType.PRIVATE:
        return True
    
    settings = await db.get_chat_settings(message.chat.id)
    if not settings.get("is_enabled", True):
        return False
    
    bot_user = await client.get_me()
    if bot_user.username and f"@{bot_user.username.lower()}" in message.text.lower():
        return True
    
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot_user.id:
            return True
            
    return False

@Client.on_message(filters.text & ~filters.bot, group=1)
async def auto_chat_handler(client: Client, message: Message):
    trigger_doc = await db.get_trigger(message.chat.id, message.text)
    if trigger_doc:
        return await message.reply_text(trigger_doc["response"])
    
    if not await should_reply(client, message):
        return
    
    bot_user = await client.get_me()
    cleaned_text = message.text
    if bot_user.username:
        cleaned_text = cleaned_text.replace(f"@{bot_user.username}", "").strip()
    
    if not cleaned_text:
        cleaned_text = "heyy"

    settings = await db.get_chat_settings(message.chat.id)
    personality = settings.get("personality", "flirty_friendly")
    
    await client.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    
    history = await db.get_chat_history(message.chat.id, limit=6)
    reply_text = await generate_gemini_reply(personality, history, cleaned_text)
    
    if not reply_text or not reply_text.strip():
        reply_text = "kuch nahi bas baithi hu u batao kya kar rhe ho?"
        
    await message.reply_text(reply_text.strip())
    await db.append_chat_history(message.chat.id, cleaned_text, reply_text.strip())
