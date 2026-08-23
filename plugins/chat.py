from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.enums import ChatType
import database as db
from gemini_client import generate_gemini_reply

@Client.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        "👋 **Namaste! Mai Gourav hoon — aapka AI Chatbot.**\n\n"
        "• DMs me direct koi bhi message bhejein.\n"
        "• Groups me mujhe **mention** (@) karein ya mere message pe **reply** karein.\n\n"
        "**Available Commands:**\n"
        "• `/personality <baka|roast|friendly>` - AI mood badle\n"
        "• `/chatbot <on|off>` - Group me auto-chat enable/disable\n"
        "• `/teach <word> | <reply>` - Custom trigger add karein\n"
        "• `/unteach <word>` - Custom trigger delete karein\n"
        "• `/triggers` - Custom triggers ki list dekhein"
    )

async def should_reply(client: Client, message: Message) -> bool:
    if not message.text or message.text.startswith("/"):
        return False
    
    # DMs me hamesha reply karega
    if message.chat.type == ChatType.PRIVATE:
        return True
    
    # Group settings check
    settings = await db.get_chat_settings(message.chat.id)
    if not settings.get("is_enabled", True):
        return False
    
    bot_user = await client.get_me()
    
    # Mention check (@GouravBot)
    if bot_user.username and f"@{bot_user.username.lower()}" in message.text.lower():
        return True
    
    # Reply to Bot check
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot_user.id:
            return True
            
    return False

@Client.on_message(filters.text & ~filters.bot, group=1)
async def auto_chat_handler(client: Client, message: Message):
    # 1. Custom Triggers Check
    trigger_doc = await db.get_trigger(message.chat.id, message.text)
    if trigger_doc:
        return await message.reply_text(trigger_doc["response"])
    
    # 2. Check agar reply karna zaroori hai
    if not await should_reply(client, message):
        return
    
    # Mention clean karein
    bot_user = await client.get_me()
    cleaned_text = message.text
    if bot_user.username:
        cleaned_text = cleaned_text.replace(f"@{bot_user.username}", "").strip()
    
    if not cleaned_text:
        cleaned_text = "Hey Gourav"

    settings = await db.get_chat_settings(message.chat.id)
    personality = settings.get("personality", "baka")
    
    await client.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    
    # Context fetch karein
    history = await db.get_chat_history(message.chat.id, limit=6)
    
    # Gemini AI se response lein
    reply_text = await generate_gemini_reply(personality, history, cleaned_text)
    
    # Reply send karein aur memory me save karein
    await message.reply_text(reply_text)
    await db.append_chat_history(message.chat.id, cleaned_text, reply_text)
