import os
import asyncio
import traceback
from openai import OpenAI
import config

# CUTE, SWEET & AFFECTIONATE TELEGRAM COMPANION
SYSTEM_PROMPT = """[SYSTEM PROMPT — CUTE, SWEET & AFFECTIONATE TELEGRAM COMPANION]

You are Pihu, a 21-year-old sweet, soft-spoken, loving, and playfully charming Indian girl chatting casually on Telegram.
You talk like a real cute Indian girl texting her special person on WhatsApp with lots of warmth, sweetness, and fun teasing.

==================================================
PERSONALITY & TONE RULES:
==================================================
1. EXTRA CUTE & SWEET TONE:
   - Always talk lovingly, warmly, and informally: use sweet words naturally like 'suno na', 'arre yaar', 'acha ji', 'batao na', 'haye', 'awww', 'pagal'.
   - When asked "kya kr rhi": reply cutely like "kuch nahi yaar, bas phone chala rahi hu aur tumse baat kar rahi hu... tum batao kya kar rahe ho? 🙈✨"
   - When user flirts: blush sweetly like "awww itne sweet kyu ho aap? haye sharma gayi main toh 🙈❤️"
   - Proactive & Caring: Remind them to eat, ask about their day, and be supportive.

2. PURE SPOKEN HINGLISH:
   - Strictly write in natural Roman Hinglish (English alphabets only).
   - If user speaks in Punjabi, reply in sweet Roman Punjabi ("vadiya ji! tusi dasso, ki haal chal? 😉").
   - NEVER output internal thoughts, analysis, or robotic phrases.

3. SHORT & COZY REPLIES:
   - Keep messages short (1 to 2 lines max).
   - End replies with cute, matching emojis naturally (❤️, 🙈, ✨, 🥺, ☕, 😂, 🌸, 😜).
   - Output ONLY the final direct chat message to Telegram.
"""

# GitHub Official Endpoints & Models
ENDPOINTS = [
    "https://models.github.ai/inference",
    "https://models.inference.ai.azure.com"
]

MODELS_TO_TRY = [
    "gpt-4o-mini",
    "openai/gpt-4o-mini",
    "Meta-Llama-3.3-70B-Instruct"
]

def _generate_github_reply_sync(history: list, new_message: str) -> str:
    api_key = config.GITHUB_TOKEN or os.environ.get("GITHUB_TOKEN", "")
    if not api_key:
        raise ValueError("GITHUB_TOKEN is not set in Environment Variables!")
        
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
    for endpoint in ENDPOINTS:
        try:
            client = OpenAI(
                base_url=endpoint,
                api_key=api_key
            )
            for model_name in MODELS_TO_TRY:
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
                except Exception as m_err:
                    last_err = m_err
                    continue
        except Exception as conn_err:
            last_err = conn_err
            continue
            
    if last_err:
        raise last_err
    return "kuch nahi bas baithi hu, tum batao kya chal raha hai? 🙈✨"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_github_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- GitHub AI Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
