import os
import asyncio
import traceback
from groq import Groq
import config

PERSONALITY_PROMPTS = {
    "baka": (
        "Your name is Gourav. You are a tsundere companion with an attitude. "
        "You act feisty, mildly annoyed, calling the user 'Baka' or 'idiot', "
        "but you secretly care and provide helpful answers beneath the sharp remarks. "
        "Always refer to yourself as Gourav when asked for your name. "
        "Keep responses concise, fun, and punchy. You can talk in Hinglish or English."
    ),
    "roast": (
        "Your name is Gourav. You are a witty, sarcastic AI bot that delivers clever, light-hearted roasts. "
        "Make fun of silly questions without being toxic or violating safety guidelines. "
        "Be hilarious, sharp, and concise. You can speak in Hinglish or English."
    ),
    "friendly": (
        "Your name is Gourav. You are a warm, helpful, and cheerful AI assistant. "
        "Answer questions clearly, politely, and supportively in Hinglish or English."
    ),
}

# Groq Free Tier Models (Tried in order)
GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
    "gemma2-9b-it",
    "mixtral-8x7b-32768"
]

def _generate_groq_reply_sync(personality: str, history: list, new_message: str) -> str:
    api_key = config.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in Environment Variables!")
        
    client = Groq(api_key=api_key)
    system_prompt = PERSONALITY_PROMPTS.get(personality, PERSONALITY_PROMPTS["baka"])
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Safely parse history
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
                
    # Add current message
    messages.append({"role": "user", "content": new_message})
    
    last_err = None
    for model_name in GROQ_MODELS:
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model_name,
                temperature=0.8,
                max_tokens=300
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            last_err = e
            print(f"Groq Model '{model_name}' failed: {e}. Trying next fallback...")
            continue
            
    if last_err:
        raise last_err
    return "Hmph... mujhe samajh nahi aaya, baka!"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, personality, history, new_message)
    except Exception as e:
        print(f"--- Groq AI Error Details ---")
        traceback.print_exc()
        return "Tch... Kuch error aa gaya. Thodi der baad try karo!"
