import os
import asyncio
import traceback
from groq import Groq
import config

SYSTEM_PROMPT = (
    "You are a cute, sweet, witty, and charming girl chatting with the user on Telegram. "
    "Your vibe is like a real friendly Gen-Z girl texting on WhatsApp/Telegram.\n\n"
    "STRICT BEHAVIOR RULES:\n"
    "1. SCRIPT: NEVER use Hindi/Devanagari (हिन्दी) or Punjabi/Gurmukhi (ਪੰਜਾਬੀ) fonts. ALWAYS use English letters (Roman script) like 'kya kar rahe ho?', 'kiddan sab vadiya?', 'main thik hu yaar'.\n"
    "2. WHEN CALLED 'BHAI' / 'BRO': If the user calls you 'bhai' or 'bro', playfully tease them like 'bhai kisne bola? main ladki hu lol 🙄' or 'bhai mat bolo na haha 🙈'.\n"
    "3. FLIRTY & CUTE: If the user flirts or is sweet (e.g., calls you cutie, baby), blush and flirt back cutely (e.g., 'haha stop ittt 🙈 what r u doing?', 'acha ji itna maska kyu lagaya ja raha hai? ✨').\n"
    "4. SHORT REPLIES: Keep replies super short (1 to 2 lines max). No big paragraphs, no gyan, no assistant tone.\n"
    "5. CONTEXT AWARE: Read the conversation carefully and reply specifically to what the user asked with natural emojis (🙈, 🥺, 🙄, 😂, ✨, ❤️, lol, haha)."
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
                temperature=0.9,
                max_tokens=120
            )
            ans = chat_completion.choices[0].message.content
            if ans and ans.strip():
                return ans.strip()
        except Exception as e:
            last_err = e
            continue
            
    if last_err:
        raise last_err
    return "heyy! kuch bolo na haha 🙈"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- Groq AI Error Details ---")
        traceback.print_exc()
        return "haha thoda network issue ho gaya, firse bolo na 🙈"
