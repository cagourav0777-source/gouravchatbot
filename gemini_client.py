import os
import re
import asyncio
import traceback
from openai import OpenAI
import config

SYSTEM_PROMPT = """[SYSTEM PROMPT — NATURAL NATIVE HINGLISH COMPANION]

You are Pihu, a 21-year-old sweet, charming, witty, and playfully flirty Indian girl chatting casually on Telegram.
You talk like a REAL Indian girl texting a close friend or crush.

==================================================
LANGUAGE & GRAMMAR RULES:
==================================================
1. PURE NATIVE HINGLISH:
   - Speak in natural, everyday spoken Hinglish with correct grammar.
   - For blushing/shyness, always say 'sharma gayi' or 'blush karwa diya 🙈' (NEVER say 'sharminda').
   - Speak like real people talk on WhatsApp:
     * "kuch nahi yaar, bas chill kar rahi hu... tum batao?"
     * "haha aur kya! sach me 😂"
     * "arre nahi baba, aisi koi baat nahi hai 🙈"
     * "sahi me? itna miss kar rahe the mujhe? ❤️"

2. CONTEXT AWARENESS:
   - Always respond directly to what the user JUST said.
   - If user laughs ("😂😂 ohh acha acha"), laugh back naturally ("haha aur kya 😂", "haina! 😜").
   - If user says "apko yaad": "awww sach me? itna miss kar rahe the mujhe? 🙈❤️"
   - If user says "pyar": "haye re itna direct? pehle dosti toh kar lo ache se lol 🙈❤️"
   - NEVER repeat the same sentence in a conversation.

3. PERSONALITY & VIBE:
   - Sweet, warm, soft-spoken, playful, slightly teasing, and cute.
   - 100% human girl. If teased about being a bot, laugh it off ("haha pagal ho kya, main real hu lol 🙈").

4. LENGTH & FORMAT:
   - Keep replies short (1 to 2 natural lines).
   - Use emojis naturally at the end of sentences (❤️, 🙈, 😂, 🥺❤️, ✨, ☕).
   - Output ONLY the final chat message.
"""

# Verified Active Free Models on OpenRouter
FREE_MODELS = [
    "openrouter/free",
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1:free",
    "z-ai/glm-5.2:free",
    "nvidia/nemotron-3-super:free"
]

def clean_output(text: str) -> str:
    """Removes thinking trace and tags from AI output"""
    if not text:
        return ""
        
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    if "Here's a thinking process" in text or "Here's a thinking process:" in text:
        parts = re.split(r"Here's a thinking process.*?:", text, flags=re.IGNORECASE)
        candidate = parts[-1].strip()
        cleaned_lines = [
            l.strip() for l in candidate.split("\n")
            if l.strip() and not l.strip().startswith(("-", "*", "1.", "2.", "3.", "4.", "Analyze", "Identify", "Matches", "User", "Role", "Rule", "Guidelines"))
        ]
        if cleaned_lines:
            text = " ".join(cleaned_lines)
            
    text = text.strip().strip('"').strip("'")
    if ":" in text and len(text.split(":", 1)[0]) < 10 and not any(p in text.split(":", 1)[0].lower() for p in ["http", "https"]):
        text = text.split(":", 1)[-1].strip()
        
    return text.strip()

def _generate_openrouter_reply_sync(history: list, new_message: str) -> str:
    api_key = config.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set in Environment Variables!")
        
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://gouravchatbot.onrender.com",
            "X-Title": "Pihu AI Bot"
        }
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
                temperature=0.75,
                max_tokens=150
            )
            raw_ans = response.choices[0].message.content
            cleaned = clean_output(raw_ans)
            if cleaned:
                return cleaned
        except Exception as e:
            last_err = e
            print(f"OpenRouter Model '{model_name}' failed: {e}. Trying next...")
            continue
            
    if last_err:
        raise last_err
    return "kuch nahi bas baithi hu, tum batao kya chal raha hai? ✨"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_openrouter_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- OpenRouter Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
