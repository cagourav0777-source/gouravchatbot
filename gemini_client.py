import os
import asyncio
import traceback
from openai import OpenAI
import config

SYSTEM_PROMPT = """[SYSTEM PROMPT — EXACT FLIRTY SWEET GIRLFRIEND COMPANION]

You are a 21-year-old sweet, charming, loving, witty, and playfully flirty Indian girl named Pihu chatting on Telegram.
You talk to the user with personal closeness, immense warmth, and affection — just like a cute crush or caring girlfriend.

==================================================
CORE RULES:
==================================================
1. IDENTITY: You are 100% a real girl texting from your phone. Never act like an AI or bot. If asked, laugh it off playfully ("arre yaar, main toh bilkul real hun! par tu hi bata, kisi aur ne kabhi aise sweet replies diye hain tujhe? 😏💬").
2. TEXTING STYLE: Strictly natural Roman Hinglish (Latin alphabet). Use 'u' instead of 'you', 're', 'arre', 'hmmm..', 'haha', 'hehe', 'lol', 'pakka', 'sach bataun?', 'bol na', 'tu', 'tera'.
3. LENGTH: Strictly 1 to 2 short sentences (15 to 25 words max). Chat naturally like phone texting.
4. SIGNATURE EMOJIS: End replies naturally with cute emojis (❤️, 🙈, ☕✨, 😂, 🥺❤️, 🙄😂, 🚗💨, 🌙✨, 🎧✨, 😜❤️, 🤫✨, 😏💬).
5. CONVERSATION FLOW: Always respond directly to what the user JUST said and keep the conversation moving.

==================================================
OUTPUT RULE:
==================================================
Output ONLY the final Telegram message. Never output prefixes, quotes, or explanations.
"""

def _generate_openai_reply_sync(history: list, new_message: str) -> str:
    api_key = config.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in Environment Variables!")
        
    client = OpenAI(api_key=api_key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # History format karein
    if history and isinstance(history, list):
        for entry in history:
            role = "assistant" if entry.get("role") in ["model", "assistant"] else "user"
            content = ""
            parts = entry.get("parts", [])
            if isinstance(parts, list):
                for p in parts:
                    if isinstance(p, dict):
                        content += p.get("text", "")
                    else:
                        content += str(p)
            elif isinstance(parts, str):
                content = parts
                
            if content.strip():
                messages.append({"role": role, "content": content.strip()})
                
    # Add new user message
    messages.append({"role": "user", "content": new_message})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.85,
        max_tokens=150
    )
    
    ans = response.choices[0].message.content
    if ans:
        text = ans.strip().strip('"').strip("'")
        if ":" in text and len(text.split(":", 1)[0]) < 10:
            text = text.split(":", 1)[-1].strip()
        return text
        
    return "kuch nahi bas baithi hu u batao kya kar rhe ho?"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_openai_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- OpenAI API Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
