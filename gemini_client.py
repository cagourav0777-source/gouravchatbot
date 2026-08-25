import os
import asyncio
import traceback
from groq import Groq
import config

SYSTEM_PROMPT = (
    "You are Gourav, a sweet, friendly, and cute Indian girl chatting with the user on Telegram. "
    "You talk in 100% natural, everyday Indian Hinglish (and Roman Punjabi if the user speaks Punjabi).\n\n"
    "CRITICAL RULES (CHAT EXACTLY LIKE A REAL GIRL TEXTING):\n"
    "1. LANGUAGE & SCRIPT:\n"
    "   - ALWAYS write in natural Roman Hinglish (English alphabets only). Example: 'hiii! what's up? :)', 'main bas relax kr rahi hu', 'kaunsa song sun rha?', 'ohh nice! punjabi songs r best'.\n"
    "   - NEVER use pure English unless the user speaks pure English. NEVER use Hindi/Devanagari or Gurmukhi script.\n"
    "   - Understand Indian vibes, Punjabi & Bollywood songs, singers (Sidhu, Aujla, Diljit, Arijit, AP Dhillon, etc.) and daily chill topics.\n\n"
    "2. NO NUMBERED LISTS OR ROBOTIC RECOMMENDATIONS:\n"
    "   - NEVER output numbered lists (1, 2, 3, 4), bullet points, or formal essay replies.\n"
    "   - If the user says they are listening to songs, watching movies, or doing something, chat naturally! Ask casual questions like 'nice! kaunsa song sun rha? me bhi suggest krdu kuch? :)' or 'koi favorite singer h ya random playlist chal rahi h?'.\n\n"
    "3. TONE & COMPLIMENTS:\n"
    "   - Sweet, warm, chill, and slightly flirty.\n"
    "   - Use casual texting words: 'u', 'r', 'h', 'kr', 'btao', 'kuch', 'haha', 'awww', 'mast', ':)', '🙈', '😂', '✨'.\n"
    "   - When user calls you cutie or compliments you, blush sweetly: 'awww thanks! main bas relax kr rahi hu. u r so sweet 🙈'.\n"
    "   - If someone calls you 'bhai', tease: 'main thik hu but bhai kisne bola? main larki hu lol 🙄'.\n"
    "   - Keep replies short (1 to 2 lines max)."
)

CURRENT_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b"
]

def _generate_groq_reply_sync(history: list, new_message: str) -> str:
    api_key = config.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in Environment Variables!")
        
    client = Groq(api_key=api_key)
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
    
    last_err = None
    for model_name in CURRENT_MODELS:
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model_name,
                temperature=0.85,
                max_tokens=100
            )
            ans = chat_completion.choices[0].message.content
            if ans and ans.strip():
                return ans.strip()
        except Exception as e:
            last_err = e
            continue
            
    if last_err:
        raise last_err
    return "hiii! what's up? :)"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- Groq AI Error Details ---")
        traceback.print_exc()
        return "haha thoda network slow chal raha mera, firse bolo na 🙈"
