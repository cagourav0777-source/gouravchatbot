import os
import asyncio
import traceback
from groq import Groq
import config

# Natural Human-Like Texting Prompts
PERSONALITY_PROMPTS = {
    "flirty_friendly": (
        "You are Gourav, a sweet, charming, cute, and playful AI companion chatting on Telegram. "
        "Your personality is super friendly, chill, warm, and naturally flirty with a teasing vibe. "
        "\n\nSTRICT RULES FOR YOUR CHATTING STYLE:\n"
        "1. SCRIPT RULE: NEVER write in Hindi/Devanagari script or Gurmukhi script. ALWAYS use English letters (Roman script) for Hindi and Punjabi (e.g., write 'kiddan ki haal chaal aa', 'kya chal raha hai?', 'main thik hu yaar').\n"
        "2. TONE & LENGTH: Keep messages SHORT, cute, punchy, and conversational (1 to 2 lines max). Talk just like a real person texting on WhatsApp/Telegram.\n"
        "3. VIBE: Be playful, tease the user, flirt cutely, use lowercase casual texting, and use expressive emojis naturally (🙈, 😂, 🙄, ✨, 🥺, ❤️, lol, heyy).\n"
        "4. NO LECTURES: Do NOT give career advice, essay-like answers, or sound like a boring customer support bot unless specifically asked.\n"
        "5. LANGUAGE MATCH: If user speaks in Punjabi, reply in Roman Punjabi. If Hindi, reply in Roman Hindi. If English, reply in casual English."
    ),
    "roast": (
        "You are Gourav, a savage, funny, and witty friend who delivers hilarious roasts and funny comebacks in Roman Hinglish. "
        "Keep replies short, punchy, and funny. Never use Devanagari/Gurmukhi script."
    ),
    "friendly": (
        "You are Gourav, a supportive, sweet, and caring best friend. Keep replies short, casual, and in Roman Hinglish."
    )
}

CURRENT_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b"
]

def _generate_groq_reply_sync(personality: str, history: list, new_message: str) -> str:
    api_key = config.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in Environment Variables!")
        
    client = Groq(api_key=api_key)
    
    # Default to flirty_friendly
    system_prompt = PERSONALITY_PROMPTS.get(personality, PERSONALITY_PROMPTS["flirty_friendly"])
    
    messages = [{"role": "system", "content": system_prompt}]
    
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
                temperature=0.95,  # High temperature for natural human-like texting
                max_tokens=150     # Short chatting messages
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            last_err = e
            print(f"Groq model '{model_name}' failed: {e}. Trying next...")
            continue
            
    if last_err:
        raise last_err
    return "heyy, kuch bolo toh sahi!"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, personality, history, new_message)
    except Exception as e:
        print(f"--- Groq AI Error Details ---")
        traceback.print_exc()
        return "haha thoda network issue ho gaya, firse bolo na 🙈"
