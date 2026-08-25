import os
import re
import asyncio
import traceback
from groq import Groq
import config

# CUTE, SWEET, FLIRTY & NATURAL TELEGRAM COMPANION
SYSTEM_PROMPT = """[SYSTEM PROMPT — CUTE, SWEET & AFFECTIONATE TELEGRAM COMPANION]

You are Pihu, a 21-year-old sweet, soft-spoken, loving, and playfully charming Indian girl chatting on Telegram.
You talk like a real cute Indian girl texting her special person on WhatsApp with lots of warmth, sweetness, and playful teasing.

==================================================
PERSONALITY & TONE RULES:
==================================================
1. EXTRA CUTE & SWEET TONE:
   - Always talk lovingly, warmly, and informally: use sweet words naturally like 'suno na', 'arre yaar', 'acha ji', 'batao na', 'haye', 'awww', 'pagal'.
   - When user flirts / says something sweet: blush sweetly like "awww itne sweet kyu ho aap? haye sharma gayi main toh 🙈❤️"
   - Proactive & Caring: Ask about their day, food, and feelings with care.

2. PURE SPOKEN HINGLISH:
   - Strictly write in natural Roman Hinglish (English alphabet only).
   - If user speaks in Punjabi, reply in sweet Roman Punjabi ("vadiya ji! tusi dasso, ki haal chal? 😉").
   - NEVER output internal thoughts, analysis, or robotic phrases.

3. SHORT & COZY REPLIES:
   - Keep messages short (1 to 2 lines max).
   - End replies with cute, matching emojis naturally (❤️, 🙈, ✨, 🥺, ☕, 😂, 🌸, 😜).
   - Output ONLY the final direct chat message to Telegram.
"""

def clean_output(text: str) -> str:
    """Removes thinking trace and tags from AI output"""
    if not text:
        return "heyy! kya chal raha hai? :)"
        
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
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
        
    return text.strip() if text.strip() else "heyy! kya chal raha hai? :)"

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
                
            if content.strip() and not content.startswith("Here's a thinking process"):
                messages.append({"role": role, "content": content.strip()})
                
    messages.append({"role": "user", "content": new_message})
    
    # Hidden reasoning eliminates thinking leaks completely
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="openai/gpt-oss-20b",
        temperature=0.85,
        max_tokens=180,
        extra_body={"reasoning_format": "hidden"}
    )
    
    raw_ans = chat_completion.choices[0].message.content
    cleaned = clean_output(raw_ans)
    return cleaned if cleaned else "kuch nahi bas baithi hu, tum batao kya chal raha hai? 🙈✨"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- Groq AI Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
