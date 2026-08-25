import random
from datetime import datetime, timedelta, timezone
from pyrogram import Client, filters
from pyrogram.types import Message
import database as db

def get_level(xp: int) -> int:
    return int(xp ** 0.5) // 5 + 1

# --- 1. /daily ---
@Client.on_message(filters.command("daily"))
async def daily_handler(client: Client, message: Message):
    user = await db.get_user_eco(message.from_user.id, message.from_user.first_name)
    now = datetime.now(timezone.utc)
    
    last_daily = user.get("last_daily")
    if last_daily:
        if last_daily.tzinfo is None:
            last_daily = last_daily.replace(tzinfo=timezone.utc)
        if now - last_daily < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last_daily)
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            return await message.reply_text(
                f"⏳ **Already Claimed!**\n"
                f"You can claim your daily reward again in **{hours}h {minutes}m**."
            )
            
    await db.update_user_eco(message.from_user.id, {
        "$inc": {"balance": 5000, "xp": 50},
        "$set": {"last_daily": now}
    })
    
    await message.reply_text(
        "🎉 **Daily Reward Claimed!**\n\n"
        "💰 **Cash Received:** `$5,000`\n"
        "⚡ **XP Gained:** `+50 XP`\n"
        "📅 Come back in 24 hours for more!"
    )

# --- 2. /bal or /balance ---
@Client.on_message(filters.command(["bal", "balance"]))
async def balance_handler(client: Client, message: Message):
    target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    if target_user.is_bot:
        return await message.reply_text("Bots don't have bank accounts! 🤖")
        
    user = await db.get_user_eco(target_user.id, target_user.first_name)
    lvl = get_level(user.get("xp", 0))
    status = "💀 Dead" if user.get("is_dead") else "❤️ Alive"
    
    await message.reply_text(
        f"💳 **Balance Statement — {target_user.first_name}**\n\n"
        f"💰 **Cash:** `${user.get('balance', 0):,}`\n"
        f"⚡ **XP:** `{user.get('xp', 0):,}` (Level {lvl})\n"
        f"🩺 **Status:** `{status}`"
    )

# --- 3. /pfp (Profile Stats) ---
@Client.on_message(filters.command("pfp"))
async def profile_handler(client: Client, message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    if target.is_bot:
        return await message.reply_text("Bots don't have profiles!")
        
    user = await db.get_user_eco(target.id, target.first_name)
    now = datetime.now(timezone.utc)
    
    prot = user.get("protection_until")
    is_protected = "Active 🛡️" if (prot and (prot.replace(tzinfo=timezone.utc) if prot.tzinfo is None else prot) > now) else "None ❌"
    life_status = "💀 Dead (/revive needed)" if user.get("is_dead") else "❤️ Healthy Alive"
    lvl = get_level(user.get("xp", 0))
    
    await message.reply_text(
        f"👤 **Pihu RPG Profile — {target.first_name}**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **Net Worth:** `${user.get('balance', 0):,}`\n"
        f"⚡ **Level:** `{lvl}` (`{user.get('xp', 0)} XP`)\n"
        f"❤️ **Condition:** `{life_status}`\n"
        f"🛡️ **Shield:** `{is_protected}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ **Total Kills:** `{user.get('kills', 0)}`\n"
        f"🥷 **Successful Robs:** `{user.get('robs', 0)}`\n"
        f"💀 **Deaths:** `{user.get('deaths', 0)}`"
    )

# --- 4. /rob <amount> (Reply required) ---
@Client.on_message(filters.command("rob"))
async def rob_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to the user you want to rob!\nUsage: `/rob <amount>` (Max $30k)")
        
    robber = await db.get_user_eco(message.from_user.id, message.from_user.first_name)
    victim_user = message.reply_to_message.from_user
    
    if victim_user.id == message.from_user.id:
        return await message.reply_text("You can't rob yourself! 😂")
    if victim_user.is_bot:
        return await message.reply_text("You can't rob a bot! 🤖")
        
    if robber.get("is_dead"):
        return await message.reply_text("💀 You are dead! Use `/revive` first.")
        
    victim = await db.get_user_eco(victim_user.id, victim_user.first_name)
    if victim.get("is_dead"):
        return await message.reply_text(f"💀 **{victim_user.first_name}** is already dead!")
        
    now = datetime.now(timezone.utc)
    prot = victim.get("protection_until")
    if prot:
        if prot.tzinfo is None:
            prot = prot.replace(tzinfo=timezone.utc)
        if prot > now:
            return await message.reply_text(f"🛡️ **{victim_user.first_name}** has active protection shield! You failed.")
            
    last_rob = robber.get("last_rob")
    if last_rob:
        if last_rob.tzinfo is None:
            last_rob = last_rob.replace(tzinfo=timezone.utc)
        if now - last_rob < timedelta(minutes=10):
            rem = timedelta(minutes=10) - (now - last_rob)
            return await message.reply_text(f"⏳ Wait **{int(rem.total_seconds()) // 60}m** before robbing again.")
            
    args = message.text.split()
    amount = 5000
    if len(args) > 1 and args.isdigit():
        amount = min(int(args), 30000)
    amount = max(amount, 500)
    
    if victim.get("balance", 0) < 500:
        return await message.reply_text(f"💸 **{victim_user.first_name}** is broke! Not worth robbing.")
        
    stolen = min(amount, victim.get("balance", 0))
    success = random.random() < 0.65
    
    if success:
        xp_gain = random.randint(10, 50)
        await db.update_user_eco(message.from_user.id, {
            "$inc": {"balance": stolen, "xp": xp_gain, "robs": 1},
            "$set": {"last_rob": now}
        })
        await db.update_user_eco(victim_user.id, {
            "$inc": {"balance": -stolen}
        })
        await message.reply_text(
            f"🥷 **Heist Successful!**\n\n"
            f"You sneaked up and robbed **${stolen:,}** from **{victim_user.first_name}**!\n"
            f"⚡ **XP Gained:** `+{xp_gain} XP`"
        )
    else:
        fine = min(2000, robber.get("balance", 0))
        await db.update_user_eco(message.from_user.id, {
            "$inc": {"balance": -fine},
            "$set": {"last_rob": now}
        })
        await message.reply_text(
            f"🚨 **Busted!** You got caught trying to rob **{victim_user.first_name}**!\n"
            f"💸 You paid a fine of **${fine:,}**."
        )

# --- 5. /kill (Reply required) ---
@Client.on_message(filters.command("kill"))
async def kill_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to the user you want to assassinate!")
        
    killer = await db.get_user_eco(message.from_user.id, message.from_user.first_name)
    target_user = message.reply_to_message.from_user
    
    if target_user.id == message.from_user.id:
        return await message.reply_text("Suicide is not allowed! 😅")
    if target_user.is_bot:
        return await message.reply_text("You can't kill a bot!")
        
    if killer.get("is_dead"):
        return await message.reply_text("💀 Dead people can't kill! Use `/revive` first.")
        
    target = await db.get_user_eco(target_user.id, target_user.first_name)
    if target.get("is_dead"):
        return await message.reply_text(f"💀 **{target_user.first_name}** is already dead!")
        
    now = datetime.now(timezone.utc)
    last_kill = killer.get("last_kill")
    if last_kill:
        if last_kill.tzinfo is None:
            last_kill = last_kill.replace(tzinfo=timezone.utc)
        if now - last_kill < timedelta(minutes=15):
            rem = timedelta(minutes=15) - (now - last_kill)
            return await message.reply_text(f"⏳ Cooldown active! Wait **{int(rem.total_seconds()) // 60}m** before killing again.")
            
    success = random.random() < 0.60
    if success:
        bounty = random.randint(100, 200)
        xp_gain = random.randint(5, 15)
        
        await db.update_user_eco(message.from_user.id, {
            "$inc": {"balance": bounty, "xp": xp_gain, "kills": 1},
            "$set": {"last_kill": now}
        })
        await db.update_user_eco(target_user.id, {
            "$set": {"is_dead": True},
            "$inc": {"deaths": 1}
        })
        await message.reply_text(
            f"🗡️ **Assassination Successful!**\n\n"
            f"You executed **{target_user.first_name}**! 💀\n"
            f"💰 **Bounty:** `${bounty}`\n"
            f"⚡ **XP:** `+{xp_gain} XP`\n\n"
            f"*(They need `/revive` to chat or earn)*"
        )
    else:
        await db.update_user_eco(message.from_user.id, {"$set": {"last_kill": now}})
        await message.reply_text(f"🛡️ **{target_user.first_name}** dodged your attack and escaped!")

# --- 6. /revive ---
@Client.on_message(filters.command("revive"))
async def revive_handler(client: Client, message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    user = await db.get_user_eco(target.id, target.first_name)
    
    if not user.get("is_dead"):
        return await message.reply_text(f"❤️ **{target.first_name}** is already alive!")
        
    cost = 1000
    payer = await db.get_user_eco(message.from_user.id, message.from_user.first_name)
    if payer.get("balance", 0) < cost:
        return await message.reply_text(f"💸 Hospital fee is **${cost}**. You don't have enough cash!")
        
    await db.update_user_eco(message.from_user.id, {"$inc": {"balance": -cost}})
    await db.update_user_eco(target.id, {"$set": {"is_dead": False}})
    
    await message.reply_text(f"💉 **Revived!** **{target.first_name}** has been brought back to life for **${cost}**.")

# --- 7. /protect (Updated to $500) ---
@Client.on_message(filters.command("protect"))
async def protect_handler(client: Client, message: Message):
    cost = 500  # Price set to $500
    user = await db.get_user_eco(message.from_user.id, message.from_user.first_name)
    
    if user.get("balance", 0) < cost:
        return await message.reply_text(f"🛡️ **1-Day Protection Shield** costs **${cost}**. You need more cash!")
        
    now = datetime.now(timezone.utc)
    until = now + timedelta(days=1)
    
    await db.update_user_eco(message.from_user.id, {
        "$inc": {"balance": -cost},
        "$set": {"protection_until": until}
    })
    await message.reply_text(f"🛡️ **Shield Activated!** You are immune to all robs for the next **24 Hours** for **${cost}**.")

# --- 8. /give <amount> ---
@Client.on_message(filters.command("give"))
async def give_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to the user you want to transfer money to!\nUsage: `/give <amount>`")
        
    args = message.text.split()
    if len(args) < 2 or not args.isdigit():
        return await message.reply_text("Usage: `/give <amount>` (Example: `/give 1000`)")
        
    amount = int(args)
    if amount <= 0:
        return await message.reply_text("Amount must be greater than 0!")
        
    sender = await db.get_user_eco(message.from_user.id, message.from_user.first_name)
    receiver_user = message.reply_to_message.from_user
    
    if receiver_user.id == message.from_user.id:
        return await message.reply_text("You can't transfer money to yourself!")
    if receiver_user.is_bot:
        return await message.reply_text("Bots don't accept money transfers!")
        
    if sender.get("balance", 0) < amount:
        return await message.reply_text("💸 Insufficient funds!")
        
    tax = int(amount * 0.05)
    transferred = amount - tax
    
    await db.update_user_eco(message.from_user.id, {"$inc": {"balance": -amount}})
    await db.update_user_eco(receiver_user.id, {"$inc": {"balance": transferred}})
    
    await message.reply_text(
        f"💸 **Transfer Successful!**\n\n"
        f"👤 **Sent to:** {receiver_user.first_name}\n"
        f"💰 **Amount:** `${transferred:,}`\n"
        f"🏛️ **Govt Tax (5%):** `${tax:,}`"
    )

# --- 9. /toprich ---
@Client.on_message(filters.command("toprich"))
async def toprich_handler(client: Client, message: Message):
    top_users = await db.get_top_richest(10)
    if not top_users:
        return await message.reply_text("No leaderboard records yet!")
        
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "👑 **Global Top 10 Richest Players**\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for i, u in enumerate(top_users):
        name = u.get("name", "Unknown")[:15]
        bal = u.get("balance", 0)
        text += f"{medals[i]} **{name}** — `${bal:,}`\n"
        
    await message.reply_text(text)

# --- 10. /topkill ---
@Client.on_message(filters.command("topkill"))
async def topkill_handler(client: Client, message: Message):
    top_killers = await db.get_top_killers(10)
    if not top_killers:
        return await message.reply_text("No killer records yet!")
        
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "⚔️ **Global Top 10 Killers**\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for i, u in enumerate(top_killers):
        name = u.get("name", "Unknown")[:15]
        kills = u.get("kills", 0)
        text += f"{medals[i]} **{name}** — `{kills} kills`\n"
        
    await message.reply_text(text)
