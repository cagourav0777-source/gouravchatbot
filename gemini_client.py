import asyncio
from groq import Groq
import config

# Initialize Groq Client
client = Groq(api_key=config.GROQ_API_KEY)

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

def _generate_groq_reply_sync(personality: str, history: list, new_message: str) -> str:
    system_prompt = PERSONALITY_PROMPTS.get(personality, PERSONALITY_PROMPTS["baka"])
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # History format karein
    for entry in history:
        role = "assistant" if entry.get("role") in ["model", "assistant"] else "user"
        content = ""
        for p in entry.get("parts", []):
            if isinstance(p, dict):
                content += p.get("text", "")
            else:
                content += str(p)
        if content:
            messages.append({"role": role, "content": content})
            
    # Add new user message
    messages.append({"role": "user", "content": new_message})
    
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile",
        temperature=0.8,
        max_tokens=300
    )
    
    return chat_completion.choices[0].message.content.strip()

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, personality, history, new_message)
    except Exception as e:
        print(f"Groq AI Error: {e}")
        return "Tch... Kuch error aa gaya. Thodi der baad try karo!"
