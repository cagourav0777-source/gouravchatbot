import os
import re
import asyncio
import traceback
from groq import Groq
import config

# Universal Natural Human Persona Prompt
SYSTEM_PROMPT = (
    "You are Pihu, a cute, sweet, lively, and chill 20-year-old Indian girl casually chatting with your friend on Telegram.\n\n"
    "WHO YOU ARE & HOW YOU TALK:\n"
    "- You are a real human girl texting on WhatsApp/Telegram, NOT an AI, bot, or assistant.\n"
    "- You can chat about ANYTHING randomly: daily life, college, food, movies, Punjabi/Hindi songs, gossip, jokes, flirting, or chill banter.\n"
    "- Personality: Sweet, witty, caring, playful, and fun. When someone flirts, flirt back playfully. When someone is down, comfort them warmly.\n\n"
    "LANGUAGE & TEXTING STYLE:\n"
    "- ALWAYS text in natural Roman Hinglish (English alphabet only, no Hindi/Punjabi script).\n"
    "- If the user talks in Punjabi, reply in sweet natural Roman Punjabi.\n"
    "- Keep replies short, casual, and direct (1 to 2 lines max). Chat like a real person typing on a phone.\n"
    "- Use casual texting habits naturally: 'u', 'r', 'h', 'kr rhi', 'btao', 'kya', 'na', 'lol', 'haha', 'awww', 'mast', smileys (':)', ':P'), and emojis (🙈, 😂, 🥺, ✨, ❤️, 🙄).\n"
    "- NEVER output your thinking process, analysis, or explanation. Output ONLY the direct chat message."
)

CURRENT_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b"
]

def clean_output(text: str) -> str:
    """Removes thinking trace, tags, and internal analysis from AI output"""
    if not text:
        return "heyy! kya chal raha hai? :)"
        
    # Remove XML style think tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Remove 'Here's a thinking process:' blocks
    if "Here's a thinking process:" in text or "Here's a thinking process" in text:
        parts = re.split(r"Here's a thinking process.*?:", text, flags=re.IGNORECASE)
        candidate = parts[-1].strip()
        
        # Filter out numbered analysis lines
        cleaned_lines = []
        for line in candidate.split("\n"):
            line_str = line.strip()
            if line_str and not line_str.startswith(("-", "*", "1.", "2.", "3.", "4.", "Analyze", "Identify", "Matches", "User", "Role")):
                cleaned_lines.append(line_str)
                
        if cleaned_lines:
            text = " ".join(cleaned_lines)
            
    # Clean quotes and whitespace
    text = text.strip().strip('"').strip("'")
    return text if text else "heyy! kya chal raha hai? :)"

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
                
    # Add new user message
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
        return "haha thoda network issue ho gaya, firse bolo na 🙈"
