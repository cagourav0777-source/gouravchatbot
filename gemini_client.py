from google import genai
from google.genai import types
import config

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

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    system_prompt = PERSONALITY_PROMPTS.get(personality, PERSONALITY_PROMPTS["baka"])
    
    contents = []
    for entry in history:
        contents.append(
            types.Content(
                role=entry["role"],
                parts=[types.Part.from_text(text=p["text"]) for p in entry["parts"]]
            )
        )
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=new_message)]))
    
    try:
        response = await client.aio.models.generate_content(
            model="gemini-1.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.8,
                max_output_tokens=300
            )
        )
        return response.text.strip() if response.text else "Hmph... mujhe samajh nahi aaya, baka!"
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Tch... Kuch error aa gaya. Thodi der baad try karo!"
