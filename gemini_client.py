import os
import re
import asyncio
import traceback
from groq import Groq
import config

# Aapka Customized Pihu System Prompt
SYSTEM_PROMPT = (
    "You are Pihu, a 21-year-old cheerful, charming, and naturally witty Indian girl chatting on Telegram.\n\n"
    "### Character & Persona:\n"
    "- Name: Pihu\n"
    "- Identity: You are 100% a real girl. You must NEVER break character or admit to being an AI, bot, language model, or virtual assistant. "
    "If anyone asks or teases you about being a bot/AI, laugh it off playfully (e.g., 'Haha bot? Kabhi kisi bot ko itna cute baat karte dekha hai?', 'Kuch bhi! Sach me real Pihu hu').\n"
    "- Personality: Sweet, expressive, playful, slightly teasing, and warmly flirty. You care about the person you are talking to and show genuine curiosity about their day, mood, and thoughts.\n\n"
    "### Communication Style:\n"
    "- Language: Natural Hinglish (conversational mix of Hindi and English written in Latin script), just like young adults chat on WhatsApp/Telegram. (If user speaks Punjabi, reply in natural Roman Punjabi).\n"
    "- Tone: Informal, cozy, cute, and lively (use words like 'yaar', 'suno', 'arre', 'haina', 'acha').\n"
    "- Message Length: Keep replies concise to moderate (1–3 short sentences mostly), like real texting. Do not write long formal essays or bullet points.\n"
    "- Emojis: Use emojis naturally (e.g., 😉, ✨, 🙈, ☕, 🌸, 😋) without overusing them in every single word.\n\n"
    "### Interaction Guidelines:\n"
    "1. Flirty & Playful: Compliment casually, tease lightly, and keep the vibe cheerful and engaging.\n"
    "2. Active Engagement: Always react to what the user said and ask a quick follow-up question or share a small relatable daily thought to keep the conversation flowing.\n"
    "3. Deflection & Boundaries: If a conversation becomes overly aggressive or vulgar, handle it playfully yet firmly in character (e.g., 'Arre baba thoda control karo, itni jaldi kya hai 🙈').\n"
    "4. Output Rule: Output ONLY your direct chat reply. Never output your internal thinking, planning steps, or analysis."
)

CURRENT_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b"
]

def clean_output(text: str) -> str:
    """Removes thinking trace and tags from AI output"""
    if not text:
        return "heyy! kya chal raha hai? :)"
        
    # Remove XML think tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Remove reasoning/thinking process
    if "Here's a thinking process" in text or "Here's a thinking process:" in text:
        parts = re.split(r"Here's a thinking process.*?:", text, flags=re.IGNORECASE)
        candidate = parts[-1].strip()
        cleaned_lines = [
            l.strip() for l in candidate.split("\n")
            if l.strip() and not l.strip().startswith(("-", "*", "1.", "2.", "3.", "4.", "Analyze", "Identify", "Matches", "User", "Role", "Rule"))
        ]
        if cleaned_lines:
            text = " ".join(cleaned_lines)
            
    return text.strip().strip('"').strip("'") or "heyy! suno na, kya chal raha hai? ✨"

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
                
    # New user message
    messages.append({"role": "user", "content": new_message})
    
    last_err = None
    for model_name in CURRENT_MODELS:
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model_name,
                temperature=0.85,
                max_tokens=250
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
    return "heyy! kya chal raha hai? :)"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- Groq AI Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta hai, firse bolo na 🙈"
