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

# Current Active Gemini Models
MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite"]

def _generate_response_sync(personality: str, history: list, new_message: str) -> str:
    system_prompt = PERSONALITY_PROMPTS.get(personality, PERSONALITY_PROMPTS["baka"])
    
    # History format karein
    formatted_contents = []
    for entry in history:
        role = entry.get("role", "user")
        parts = []
        for p in entry.get("parts", []):
            text_val = p.get("text", "") if isinstance(p, dict) else str(p)
            if text_val:
                parts.append(types.Part.from_text(text=text_val))
        if parts:
            formatted_contents.append(types.Content(role=role, parts=parts))
            
    # Latest user message add karein
    formatted_contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=new_message)])
    )
    
    config_obj = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.8,
        max_output_tokens=300
    )
    
    # Available models try karein
    last_error = None
    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=formatted_contents,
                config=config_obj
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            last_error = e
            print(f"Model {model_name} failed: {e}. Trying next model...")
            continue
            
    if last_error:
        raise last_error
    return "Hmph... mujhe samajh nahi aaya, baka!"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_response_sync, personality, history, new_message)
    except Exception as e:
        print(f"Gemini API All Models Error: {e}")
        return "Tch... Kuch error aa gaya. Thodi der baad try karo!"
