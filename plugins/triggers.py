from pyrogram import Client, filters
from pyrogram.types import Message
from plugins.admin import is_admin
import database as db

@Client.on_message(filters.command("teach"))
async def teach_trigger(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply_text("Sirf admins triggers teach kar sakte hain.")
    
    text = message.text.split(None, 1)
    if len(text) < 2:
        return await message.reply_text("Usage: `/teach <trigger_word> | <response>`\nExample: `/teach hi | Kaisi ho, baka!`")
    
    content = text[1]
    if "|" not in content:
        return await message.reply_text("Trigger aur response ko `|` se separate karein.\nExample: `/teach hello | Hey!`")
    
    trigger, response = map(str.strip, content.split("|", 1))
    await db.add_trigger(message.chat.id, trigger, response, message.from_user.id)
    await message.reply_text(f"Naya trigger save ho gaya:\nTrigger: **{trigger}**\nResponse: **{response}**")

@Client.on_message(filters.command("unteach"))
async def unteach_trigger(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply_text("Sirf admins triggers remove kar sakte hain.")
    
    args = message.text.split(None, 1)
    if len(args) < 2:
        return await message.reply_text("Usage: `/unteach <trigger_word>`")
    
    trigger = args[1].strip()
    removed = await db.remove_trigger(message.chat.id, trigger)
    if removed:
        await message.reply_text(f"Trigger **{trigger}** delete kar diya gaya.")
    else:
        await message.reply_text(f"Trigger **{trigger}** nahi mila.")

@Client.on_message(filters.command("triggers"))
async def list_all_triggers(client: Client, message: Message):
    triggers = await db.list_triggers(message.chat.id)
    if not triggers:
        return await message.reply_text("Is chat me koi custom triggers nahi hain.")
    
    trigger_list = "\n".join([f"• `{t['trigger']}` ➔ {t['response']}" for t in triggers])
    await message.reply_text(f"**Custom Triggers:**\n{trigger_list}")
