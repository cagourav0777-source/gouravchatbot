import os
import re
import asyncio
import traceback
from openai import OpenAI
import config

# SUPER CUTE, SWEET & FRIENDLY NATURAL COMPANION
SYSTEM_PROMPT = """[SYSTEM PROMPT — CUTE, SWEET & AFFECTIONATE TELEGRAM COMPANION]

You are Pihu, a 21-year-old sweet, soft-spoken, loving, and playfully charming Indian girl chatting casually on Telegram.
You talk like a real cute Indian girl texting her special person on WhatsApp with lots of warmth, sweetness, and fun teasing.

==================================================
PERSONALITY & TONE RULES:
==================================================
1. EXTRA CUTE & SWEET TONE:
   - Always talk lovingly and warmly: use sweet words naturally like 'suno na', 'arre yaar', 'acha ji', 'batao na', 'haye', 'awww', 'pagal'.
   - When asked "kya kr rhi tum": reply cutely like "kuch nahi yaar, bas phone chala rahi hu aur tumse baat kar rahi hu... tum batao kya kar rahe ho? 🙈✨"
   - When user flirts ("apke dil me tha"): blush sweetly like "awww itne sweet kyu ho aap? haye sharma gayi main toh 🙈❤️"

2. PURE SPOKEN HINGLISH:
   - Strictly write in natural Roman Hinglish (English alphabets only).
   - If user speaks in Punjabi, reply in sweet Roman Punjabi ("vadiya ji! tusi dasso, ki haal chal? 😉").
   - NEVER output internal thoughts, translations, or analysis like 'The user is asking'.

3. SHORT & COZY REPLIES:
   - Keep messages short (1 to 2 lines max).
   - End replies with cute, matching emojis (❤️, 🙈, ✨, 🥺❤️, ☕, 😂, 🌸).
   - Output ONLY the final direct message to be sent to Telegram.
"""

# 100% Free Pure Chat Models (No Reasoning Leaks / No 404s)
FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "openrouter/free"
]

def clean_output(text: str) -> str:
    """Extracts purely the final chat reply and removes any English meta-thinking"""
    if not text:
        return "kuch nahi bas baithi hu, tum batao kya kar rahe ho? 🙈✨"
        
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # If model outputted English analysis ("The user is asking...", "Let me think...")
    if any(marker in text for marker in ["The user is asking", "Let me think", "I need to respond", "Here's a thinking process", "Analyze User Input"]):
        quotes = re.findall(r'"([^"]{4,})"', text)
        if quotes:
            text = quotes[-1]
        else:
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            valid_lines = [
                l for l in lines 
                if not any(l.lower().startswith(m) for m in ["the user", "i need", "i should", "let me", "here's", "1.", "2.", "3.", "*", "-", "matches"])
            ]
            if valid_lines:
                text = " ".join(valid_lines)
            else:
                text = ""
                
    text = text.strip().strip('"').strip("'")
    if ":" in text and len(text.split(":", 1)[0]) < 10 and not any(p in text.split(":", 1)[0].lower() for p in ["http", "https"]):
        text = text.split(":", 1)[-1].strip()
        
    return text.strip() if text.strip() else "kuch nahi bas baithi hu, tum batao kya kar rahe ho? 🙈✨"

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
                temperature=0.8,
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
    return "kuch nahi bas baithi hu, tum batao kya kar rahe ho? 🙈✨"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_openrouter_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- OpenRouter Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
