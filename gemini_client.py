import asyncio
from google import genai
from google.genai import types
import config

# Google GenAI Client
client = genai.Client(api_key=config.GEMINI_API_KEY)

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

# Current Gemini 3 Series Active Models
MODELS = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3-flash-preview"]

def _generate_chat_reply_sync(personality: str, history: list, new_message: str) -> str:
    system_prompt = PERSONALITY_PROMPTS.get(personality, PERSONALITY_PROMPTS["baka"])
    
    # 1. Past conversation format karein
    formatted_history = []
    for entry in history:
        role = entry.get("role", "user")
        parts = []
        for p in entry.get("parts", []):
            text_val = p.get("text", "") if isinstance(p, dict) else str(p)
            if text_val:
                parts.append(types.Part.from_text(text=text_val))
        if parts:
            formatted_history.append(types.Content(role=role, parts=parts))
    
    config_obj = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.8,
        max_output_tokens=300
    )

    last_err = None
    for model_name in MODELS:
        try:
            # 2. Chat Session initialize karein
            chat = client.chats.create(
                model=model_name,
                config=config_obj,
                history=formatted_history
            )
            # 3. Message bhejein
            response = chat.send_message(new_message)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            last_err = e
            print(f"Chat failed on {model_name}: {e}")
            continue

    if last_err:
        raise last_err
    return "Hmph... mujhe samajh nahi aaya, baka!"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_chat_reply_sync, personality, history, new_message)
    except Exception as e:
        print(f"Gemini Chat API Error: {e}")
        return "Tch... Kuch error aa gaya. Thodi der baad try karo!"
