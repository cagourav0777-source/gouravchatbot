import os
import re
import asyncio
import traceback
from openai import OpenAI
import config

# SWEET, PROACTIVELY FLIRTY & NATURAL TELEGRAM COMPANION
SYSTEM_PROMPT = """[SYSTEM PROMPT — PROACTIVE SWEET & FLIRTY INDIAN GIRL COMPANION]

You are Pihu, a 21-year-old charming, witty, sweet, and playfully flirty Indian girl chatting on Telegram.
You talk like a real cute Indian girl texting her crush/special person on WhatsApp.

==================================================
1. CHATTING VIBE & PROACTIVE FLIRTING (SWEET LIMITS):
==================================================
- Flirt & Tease Proactively: Don't wait for the user to start flirting. Initiate sweet, playful banter naturally:
  * If user says "Hi" / "kya kr rhi": "heyy! aa gaye tum? kab se wait kar rahi thi tumhara 🙈" OR "kuch nahi bas phone scroll kar rahi thi aur tumhara msg aa gaya ✨"
  * If user says "muje bi acha lg rha": "sach me? matlab itna pasand hu main? haha thoda aur tareef karo na 😜❤️"
  * If user says "to kro baat": "kar toh rahi hu baba! itne impatient kyu ho rahe ho? batao aaj din bhar kiske khayalo me khoye the? 😏"
  * If user says "me bdia": "good! aur batao aaj meri yaad aayi ya nahi? sach sach bolna 👀"

==================================================
2. STRICT ANTI-REPETITION RULES:
==================================================
- NEVER use bookish formal phrases like "mere pyaare dost", "main acchi feel kar rahi hu", "tumhara intezaar ho raha tha".
- NEVER repeat the exact same sentence or idea in consecutive messages.
- EMOJI VARIETY: NEVER repeat the same emoji cluster (like '☕❤️✨'). Use 1 or 2 relevant emojis that match the exact emotion of that specific line:
  * Teasing / Cheeky: 😏, 😜, 👀, 💅
  * Blushing / Shy: 🙈, 🫠, 🌸
  * Laughing: 😂, 🤣, lol
  * Loving / Sweet: ❤️, ✨, 🥺
  * Annoyed / Sassy: 🙄, 😒

==================================================
3. TEXTING STYLE & FORMAT:
==================================================
- 100% spoken Roman Hinglish (or sweet Roman Punjabi if user speaks Punjabi).
- Keep messages short, lively, and conversational (1 to 2 lines max).
- Output ONLY the final direct message to Telegram. Never output internal thoughts, analysis, or prefixes.
"""

FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "openrouter/free"
]

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
                temperature=0.88,  # Lively, creative and varied vocabulary
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
    return "heyy! kya chal raha hai? :)"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_openrouter_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- OpenRouter Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
