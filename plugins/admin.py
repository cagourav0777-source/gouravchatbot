from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ChatType
import database as db

async def is_admin(client: Client, message: Message) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return True
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]

@Client.on_message(filters.command("chatbot") & filters.group)
async def toggle_chatbot(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply_text("Ye command sirf admins ke liye hai!")
    
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ["on", "off"]:
        return await message.reply_text("Usage: `/chatbot on` ya `/chatbot off`")
    
    status = args[1].lower() == "on"
    await db.update_chat_settings(message.chat.id, {"is_enabled": status})
    state = "enabled (ON)" if status else "disabled (OFF)"
    await message.reply_text(f"Gourav AI Chatbot ab is group me **{state}** hai.")

@Client.on_message(filters.command("personality"))
async def set_personality(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply_text("Ye setting change karne ke liye admin hona zaroori hai.")
    
    args = message.text.split()
    valid_modes = ["baka", "roast", "friendly"]
    if len(args) < 2 or args[1].lower() not in valid_modes:
        modes_str = ", ".join([f"`{m}`" for m in valid_modes])
        return await message.reply_text(f"Usage: `/personality <mode>`\nAvailable modes: {modes_str}")
    
    mode = args[1].lower()
    await db.update_chat_settings(message.chat.id, {"personality": mode})
    await message.reply_text(f"Personality change ho gayi: **{mode.capitalize()}** mode.")
