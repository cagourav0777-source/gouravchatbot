import asyncio
from google import genai
from google.genai import types
import config

# Naya Google GenAI Client initialize karein
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

def _generate_chat_response(personality: str, history: list, new_message: str) -> str:
    system_prompt = PERSONALITY_PROMPTS.get(personality, PERSONALITY_PROMPTS["baka"])
    
    # History format karein
    formatted_history = []
    for entry in history:
        role = entry.get("role", "user")
        parts_list = []
        for p in entry.get("parts", []):
            text_val = p.get("text", "") if isinstance(p, dict) else str(p)
            if text_val:
                parts_list.append(types.Part.from_text(text=text_val))
        if parts_list:
            formatted_history.append(types.Content(role=role, parts=parts_list))
            
    # Google GenAI Chat Session start karein
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.8,
            max_output_tokens=300
        ),
        history=formatted_history
    )
    
    response = chat.send_message(new_message)
    return response.text.strip() if response.text else "Hmph... mujhe samajh nahi aaya, baka!"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        # Non-blocking async execution
        return await asyncio.to_thread(_generate_chat_response, personality, history, new_message)
    except Exception as e:
        print(f"Primary Gemini API Error: {e}")
        # Fallback to gemini-1.5-flash if needed
        try:
            def _fallback():
                system_prompt = PERSONALITY_PROMPTS.get(personality, PERSONALITY_PROMPTS["baka"])
                chat = client.chats.create(
                    model="gemini-1.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.8,
                        max_output_tokens=300
                    )
                )
                res = chat.send_message(new_message)
                return res.text.strip()
            return await asyncio.to_thread(_fallback)
        except Exception as err:
            print(f"Gemini Fallback Error: {err}")
            return "Tch... Kuch error aa gaya. Thodi der baad try karo!"
