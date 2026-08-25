import re
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType
import database as db
from gemini_client import generate_gemini_reply

# --- ENGLISH TEXT & MENUS ---
START_TEXT = (
    "Hey there! I am **Pihu** ✨\n\n"
    "Your sweet, lively, and naturally conversational AI companion.\n"
    "• Chat with me directly in DMs\n"
    "• Add me to your group chats to keep conversations active and fun\n\n"
    "Click the buttons below to explore 👇"
)

HELP_TEXT = (
    "📖 **Pihu AI — Commands Guide:**\n\n"
    "• `/clear` or `/reset` — Clear recent conversation memory\n"
    "• `/chatbot on|off` — Toggle bot auto-chat in groups (Admin only)\n"
    "• `/teach <trigger> | <response>` — Add custom trigger reply (Admin only)\n"
    "• `/unteach <trigger>` — Remove a custom trigger (Admin only)\n"
    "• `/triggers` — View all active triggers in the chat\n\n"
    "✨ *Simply send a message or say 'Pihu' in groups to chat!*"
)

def get_start_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Me To Your Group", url=f"https://t.me/{bot_username}?startgroup=true")
        ],
        [
            InlineKeyboardButton("📖 Commands", callback_data="help_menu"),
            InlineKeyboardButton("🧹 Clear Memory", callback_data="clear_memory")
        ],
        [
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Cagourav_18")
        ]
    ])

def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_start")]
    ])

# --- COMMAND HANDLERS ---
@Client.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    bot_user = await client.get_me()
    await message.reply_text(
        text=START_TEXT,
        reply_markup=get_start_keyboard(bot_user.username)
    )

@Client.on_message(filters.command(["clear", "reset"]))
async def clear_history_handler(client: Client, message: Message):
    await db.clear_chat_history(message.chat.id)
    await message.reply_text("✨ Conversation history cleared successfully! Let's start fresh.")

# --- INLINE BUTTON CALLBACKS ---
@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    bot_user = await client.get_me()
    data = query.data

    if data == "help_menu":
        await query.message.edit_text(text=HELP_TEXT, reply_markup=get_back_keyboard())
    elif data == "clear_memory":
        await db.clear_chat_history(query.message.chat.id)
        await query.answer("✨ Memory cleared successfully!", show_alert=True)
    elif data == "back_start":
        await query.message.edit_text(text=START_TEXT, reply_markup=get_start_keyboard(bot_user.username))

# --- CORE CHAT LOGIC ---
async def should_reply(client: Client, message: Message) -> bool:
    if not message.text or message.text.startswith("/"):
        return False
    
    # 1. DMs me hamesha reply karega
    if message.chat.type == ChatType.PRIVATE:
        return True
    
    # 2. Check agar group me chatbot enable hai
    settings = await db.get_chat_settings(message.chat.id)
    if not settings.get("is_enabled", True):
        return False
    
    bot_user = await client.get_me()
    
    # 3. Mention check (@BotUsername)
    if bot_user.username and f"@{bot_user.username.lower()}" in message.text.lower():
        return True
    
    # 4. Reply to bot's message check
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot_user.id:
            return True
            
    # 5. "Pihu" / "Pihuu" name call check (Direct name bolne par reply karega)
    if re.search(r'\bpihu+\b', message.text, re.IGNORECASE):
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
        reply_text = "haan bol na, sun rahi hu ✨"
        
    await message.reply_text(reply_text.strip())
    await db.append_chat_history(message.chat.id, cleaned_text, reply_text.strip())
