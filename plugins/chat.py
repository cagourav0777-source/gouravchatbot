import re
import random
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.types import InputStickerSetShortName
import database as db
from gemini_client import generate_gemini_reply

# --- CACHED CUTE STICKER PACKS (Auto-loaded from Telegram) ---
_LOADED_STICKERS = []

POPULAR_CUTE_PACKS = [
    "PeachGoma_Love",
    "MochiMochiCat",
    "peachandgoma",
    "QubyLove"
]

# Curated Fallback Stickers by Mood
STICKER_MOODS = {
    "love": [
        "CAACAgIAAxkBAAEK9zNlK2sR1F3L9x0O3gAB1yZ9qK0AAgEAA8GcYKm8n1_y7G-oDTME",
        "CAACAgIAAxkBAAEK9zVlK2sZ8k7A7j_o1N4Z8qK0AAgEAA8GcYKm8n1_y7G-oDTME",
        "CAACAgIAAxkBAAEK9zdlK2sg9m8B8l_p2N5a9rK0AAgEAA8GcYKm8n1_y7G-oDTME"
    ],
    "laugh": [
        "CAACAgIAAxkBAAEK9ztlK2sw1o-D0n_r4N7c1tK0AAgEAA8GcYKm8n1_y7G-oDTME",
        "CAACAgIAAxkBAAEK9z1lK2s42p_E1o_s5N8d2uK0AAgEAA8GcYKm8n1_y7G-oDTME"
    ],
    "sad": [
        "CAACAgIAAxkBAAEK9zdlK2sg9m8B8l_p2N5a9rK0AAgEAA8GcYKm8n1_y7G-oDTME"
    ],
    "tease": [
        "CAACAgIAAxkBAAEK9zllK2so0n9C9m_q3N6b0sK0AAgEAA8GcYKm8n1_y7G-oDTME"
    ]
}

# --- ENGLISH TEXT & MENUS ---
START_TEXT = (
    "Hey there! I am **Pihu** ✨\n\n"
    "Your sweet, lively, and naturally conversational AI companion.\n"
    "🎁 Use `/claim` to get your **$10,000 Welcome Bonus Cash**!\n\n"
    "• Chat with me directly in DMs\n"
    "• Add me to your groups to play RPG & Economy games\n\n"
    "Click the buttons below to explore 👇"
)

HELP_TEXT = (
    "📖 **Pihu AI & Economy Commands Guide:**\n\n"
    "💰 **Economy & RPG:**\n"
    "• `/claim` — Claim your $10,000 Welcome Gift (One-time)\n"
    "• `/daily` — Claim $5,000 + 50 XP daily\n"
    "• `/bal` — Check cash & XP (reply or self)\n"
    "• `/pfp` — Check profile stats, kills, robs & shield\n"
    "• `/rob <reply> <amount>` — Rob another user (Max $30k)\n"
    "• `/kill <reply>` — Assassinate a user for bounty\n"
    "• `/revive` — Revive yourself or a dead friend ($1,000)\n"
    "• `/protect` — Buy 1-day anti-rob shield ($500)\n"
    "• `/give <reply> <amount>` — Send cash (5% tax)\n"
    "• `/toprich` — Top 10 richest leaderboard\n"
    "• `/topkill` — Top 10 killers leaderboard\n\n"
    "⚙️ **Custom Triggers:**\n"
    "• `/teach <trigger> | <response>` — Add custom trigger (Admin only)\n"
    "• `/unteach <trigger>` — Remove custom trigger (Admin only)\n"
    "• `/triggers` — View all active triggers in the chat\n\n"
    "✨ *Simply send a message, sticker, or say 'Pihu' in groups!*"
)

def get_start_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Me To Your Group", url=f"https://t.me/{bot_username}?startgroup=true")
        ],
        [
            InlineKeyboardButton("📖 Commands & Help", callback_data="help_menu")
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

# --- INLINE BUTTON CALLBACKS ---
@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    bot_user = await client.get_me()
    data = query.data

    if data == "help_menu":
        await query.message.edit_text(text=HELP_TEXT, reply_markup=get_back_keyboard())
    elif data == "back_start":
        await query.message.edit_text(text=START_TEXT, reply_markup=get_start_keyboard(bot_user.username))

# --- SMART CUTE STICKER REPLY HANDLER ---
async def load_stickers_if_needed(client: Client):
    global _LOADED_STICKERS
    if _LOADED_STICKERS:
        return
    for pack in POPULAR_CUTE_PACKS:
        try:
            sticker_set = await client.invoke(
                GetStickerSet(
                    stickerset=InputStickerSetShortName(short_name=pack),
                    hash=0
                )
            )
            if sticker_set and sticker_set.documents:
                for doc in sticker_set.documents:
                    _LOADED_STICKERS.append(doc)
        except Exception:
            continue

@Client.on_message(filters.sticker & ~filters.bot)
async def sticker_handler(client: Client, message: Message):
    is_dm = message.chat.type == ChatType.PRIVATE
    bot_user = await client.get_me()
    is_reply_to_bot = (
        message.reply_to_message 
        and message.reply_to_message.from_user 
        and message.reply_to_message.from_user.id == bot_user.id
    )

    if not (is_dm or is_reply_to_bot):
        return

    await client.send_chat_action(message.chat.id, enums.ChatAction.CHOOSE_STICKER)
    
    # 1. Try loading cute sticker from public packs
    await load_stickers_if_needed(client)
    
    # 2. Pick a cute sticker that is DIFFERENT from the user's sticker
    chosen_sticker = None
    if _LOADED_STICKERS:
        chosen_doc = random.choice(_LOADED_STICKERS)
        # Verify it's not the same sticker file
        if str(getattr(chosen_doc, 'id', '')) != str(getattr(message.sticker, 'file_unique_id', '')):
            chosen_sticker = chosen_doc
            
    # 3. Fallback by mood if pack load failed
    if not chosen_sticker:
        emoji = message.sticker.emoji or ""
        if any(e in emoji for e in ["❤️", "💖", "💕", "🥰", "😘", "😍", "🙈"]):
            chosen_sticker = random.choice(STICKER_MOODS["love"])
        elif any(e in emoji for e in ["😂", "🤣", "😆", "😹", "😜"]):
            chosen_sticker = random.choice(STICKER_MOODS["laugh"])
        elif any(e in emoji for e in ["😭", "😢", "🥺", "😔", "💔"]):
            chosen_sticker = random.choice(STICKER_MOODS["sad"])
        else:
            chosen_sticker = random.choice(STICKER_MOODS["tease"])

    try:
        if chosen_sticker:
            await message.reply_cached_media(chosen_sticker)
    except Exception:
        try:
            # Fallback to direct mood sticker ID
            fallback_id = random.choice(STICKER_MOODS["love"])
            await message.reply_sticker(fallback_id)
        except Exception:
            pass

# --- CORE CHAT LOGIC ---
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
