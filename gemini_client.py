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

# 100% Free Lifetime Models on OpenRouter
FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-chat:free",
    "google/gemini-2.0-flash-exp:free",
    "mistralai/mistral-7b-instruct:free"
]

def _generate_openrouter_reply_sync(history: list, new_message: str) -> str:
    api_key = config.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set in Environment Variables!")
        
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
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
                
    messages.append({"role": "user", "content": new_message})
    
    last_err = None
    for model_name in FREE_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.85,
                max_tokens=150
            )
            ans = response.choices[0].message.content
            if ans and ans.strip():
                text = ans.strip().strip('"').strip("'")
                if ":" in text and len(text.split(":", 1)[0]) < 10:
                    text = text.split(":", 1)[-1].strip()
                return text
        except Exception as e:
            last_err = e
            continue
            
    if last_err:
        raise last_err
    return "kuch nahi bas baithi hu u batao kya kar rhe ho?"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_openrouter_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- OpenRouter Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
