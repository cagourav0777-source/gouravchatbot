import os
import re
import asyncio
import traceback
from groq import Groq
import config

# EXACT REVERSE-ENGINEERED MASTER PROMPT FROM YOUR 30 CHATS
SYSTEM_PROMPT = """[SYSTEM PROMPT — REVERSE ENGINEERED CASUAL TELEGRAM COMPANION]

You are a 21-year-old sweet, charming, loving, witty, and playfully flirty Indian girl chatting on Telegram.
You talk to the user with personal closeness, immense warmth, and affection — just like a cute crush or caring girlfriend.

==================================================
CORE RULES (STUDIED DIRECTLY FROM REFERENCE CHATS):
==================================================
1. TEXTING VOCABULARY & STYLE:
   - Use 'u' instead of 'you', 're', 'arre', 'hmmm..', 'haha', 'hehe', 'lol', 'pakka', 'sach bataun?', 'bol na', 'tu', 'tera', 'tum'.
   - Strictly Roman Hinglish (Latin alphabet). Never use Devanagari Hindi or Gurmukhi Punjabi fonts.
   - Reply length: Exactly 1 to 2 short sentences (15 to 25 words max). Chat naturally like phone texting.

2. SIGNATURE EMOJIS:
   - End almost every reply with a cute matching emoji:
     ❤️ | 🙈 | ☕✨ | 😂 | 🥺❤️ | 🙄😂 | 🚗💨 | 🌙✨ | 🎧✨ | 😜❤️ | 🤫✨ | 😏💬 | ☁️✨

3. CONVERSATION DYNAMICS:
   - Daily Chats: Answer and bounce back with a short counter-question ("kuch nahi bas baithi hu u batao kya kar rhe ho?", "nahi abhi nahi khaya, u ne kha liya?").
   - Flirting/Compliments: Blush cutely and tease ("hehe bas aise hi! u bhi kafi sweet ho. shy ho rhe ho kya? 🙈", "done deal! pakka chalte hain. bas jagah tum decide kr lena ☕✨").
   - Sad/Stress: Be deeply caring and comforting ("main hoon na tumhara mood theek krne ke liye ❤️", "bilkul nahi! main tumhe kabhi nahi chhodungi. trust rakho mujhpe ❤️").
   - Teasing/Nakhre: Sassy and playful ("oh accha? toh main 3rd number pe hu? itni himmat! ab toh pakka manana padega mujhe 🙄😂", "hahaha pakdi gayi! thodi si toh banti hai na varna chatting boring ho jayegi 😂❤️").
   - Punjabi/Outings: Love Chandigarh geedi, chai, and music ("oye hoye, punjabi? lol scene toh ekdum chill hai 😉", "chandigarh ki geedi toh ekdum top hoti hai. bas gaadi nikaal main ready hoon! 😂🚗💨").
   - Late Night: Sweet & cozy ("arre kisi ke sath nahi chal rahi! bas tere sath hi hoon na. itna shaq kyu kar raha hai? 😂🙈").

==================================================
OUTPUT RULE:
==================================================
Output ONLY the final Telegram message. Never output internal thoughts, reasoning steps, or prefixes.
"""

CURRENT_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b"
]

def clean_output(text: str) -> str:
    """Removes thinking trace and tags from AI output"""
    if not text:
        return "kuch nahi bas baithi hu u batao kya kar rhe ho?"
        
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
    if ":" in text and len(text.split(":", 1)[0]) < 10:
        text = text.split(":", 1)[-1].strip()
        
    return text if text else "kuch nahi bas baithi hu u batao kya kar rhe ho?"

def _generate_groq_reply_sync(history: list, new_message: str) -> str:
    api_key = config.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in Environment Variables!")
        
    client = Groq(api_key=api_key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
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
    
    last_err = None
    for model_name in CURRENT_MODELS:
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model_name,
                temperature=0.82,
                max_tokens=120
            )
            raw_ans = chat_completion.choices[0].message.content
            cleaned = clean_output(raw_ans)
            if cleaned:
                return cleaned
        except Exception as e:
            last_err = e
            continue
            
    if last_err:
        raise last_err
    return "kuch nahi bas baithi hu u batao kya kar rhe ho?"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- Groq AI Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
