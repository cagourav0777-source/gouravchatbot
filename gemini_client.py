import google.generativeai as genai
import config

# Gemini configure karein
genai.configure(api_key=config.GEMINI_API_KEY)

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
    
    try:
        # Generative Model initialize karein
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt,
            generation_config={
                "temperature": 0.8,
                "max_output_tokens": 300
            }
        )
        
        # History format karein
        formatted_contents = []
        for entry in history:
            role = "user" if entry.get("role") == "user" else "model"
            parts = [p.get("text", "") for p in entry.get("parts", []) if "text" in p]
            if parts:
                formatted_contents.append({"role": role, "parts": parts})
        
        # Naya message add karein
        formatted_contents.append({"role": "user", "parts": [new_message]})
        
        # Async response generate karein
        response = await model.generate_content_async(formatted_contents)
        
        if response and response.text:
            return response.text.strip()
        else:
            return "Hmph... mujhe samajh nahi aaya, baka!"
            
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Tch... Kuch error aa gaya. Thodi der baad try karo!"
