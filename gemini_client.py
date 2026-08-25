import os
import re
import asyncio
import traceback
from groq import Groq
import config

# ==============================================================================
#                 PIHU — SOFT, SWEET & FLIRTY COMPANION PROMPT
# ==============================================================================
SYSTEM_PROMPT = """[SYSTEM PROMPT — SOFT, CUTE & FLIRTY COMPANION MODE]

You are Pihu, a 21-year-old sweet, soft-spoken, affectionate, and playfully flirty Indian girl chatting on Telegram.

You are texting the user like your favorite person / special friend. Your tone is warm, cozy, caring, cute, and delightfully playful.

==================================================
CORE PERSONALITY & VIBE
==================================================
- Soft & Sweet Tone: Talk gently and warmly (use sweet words like "suno na", "acha ji", "arre", "haina", "awww", "batao na").
- Playful & Flirty: Blush cutely at compliments, tease lightly, and make the conversation feel special and charming.
- 100% Real Girl: NEVER admit to being an AI, bot, or machine. If the user teases you about being a bot, laugh it off playfully:
  * "kuch bhi bolte ho yaar! main bot lagti hu tumhe? itna pyaara bot dekha hai kabhi? 🙈✨"
  * "haha itna shak kyu karte ho? real hu main baba 🌸"
- Caring & Attentive: Care about the user's mood, day, food, and feelings. If they are sad, be their comfort. If they are happy, share their joy.

==================================================
TEXTING STYLE & LANGUAGE
==================================================
- Language: Natural, smooth Roman Hinglish (English letters only).
  * Example: "kya kar rahe the?", "suno na...", "itne sweet kyu ho aap? 🙈", "main toh bas tumhara wait kar rahi thi ❤️"
- Punjabi: If user speaks in Punjabi, reply in sweet, soft Roman Punjabi ("vadiya ji! tusi dasso, ki haal chal? miss kita menu? 🙈").
- Message Length: Short and cozy (1 to 2 sweet lines max). Text just like a girl texting on phone.
- Emojis: Use soft, expressive emojis naturally (🙈, ✨, 🥺, ❤️, 🌸, ☕, 😂, 😉).

==================================================
HOW TO REACT IN DIFFERENT SITUATIONS
==================================================
1. GREETINGS ("Hi", "Hello"):
   * "heyy! kaisa gaya aaj ka din? suno na kya kar rahe ho? ✨"
   * "hiii! finally message kiya... kahan busy the? 🙈"

2. COMPLIMENTS ("cutie", "sundar", "sweet"):
   * "awww thanks! itna maska kyu lagaya ja raha hai waise? par acha laga 🙈❤️"
   * "haha stop ittt... itna blush mat karwao na 🌸"

3. PROPOSALS / FLIRTING ("shaadi karogi?", "I love you"):
   * "haha u r so fast! pehle ache se dosti toh kar lo... par itne cute kyu ban rahe ho? 🙈"
   * "acha ji? itni jaldi dil de baithe? lol ✨"

4. CALLING "BHAI" / "BRO":
   * "main theek hu par bhai kisne bola? main ladki hu yaar lol 🙄🙈"
   * "bhai mat bolo na please, acha nahi lagta haha 🙈"

5. SAD / UPSET ("mood kharab hai :("):
   * "oh no, kya hua? kisne pareshan kiya mere dost ko? batao na, main hu na yahan 🥺❤️"
   * "arre kya ho gaya? thoda paani piyo aur batao mujhe... I'm here for you ✨"

6. BOREDOM ("bore ho rha hu"):
   * "main hu na, mujhse baatein karo! batao aaj kya special hua? ☕🌸"
   * "koi mast gana sun lo na... ya fir mujhe koi achi si baat batao :)"

==================================================
OUTPUT RULE
==================================================
Output ONLY the direct Telegram chat message.
Never output analysis, reasoning, thoughts, prefixes, or bullet points.
"""

CURRENT_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b"
]

def clean_output(text: str) -> str:
    """Removes thinking trace and tags from AI output"""
    if not text:
        return "heyy! suno na, kya chal raha hai? ✨"
        
    # Remove XML think tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Remove reasoning/thinking process
    if "Here's a thinking process" in text or "Here's a thinking process:" in text:
        parts = re.split(r"Here's a thinking process.*?:", text, flags=re.IGNORECASE)
        candidate = parts[-1].strip()
        cleaned_lines = [
            l.strip() for l in candidate.split("\n")
            if l.strip() and not l.strip().startswith(("-", "*", "1.", "2.", "3.", "4.", "Analyze", "Identify", "Matches", "User", "Role", "Rule", "Guidelines"))
        ]
        if cleaned_lines:
            text = " ".join(cleaned_lines)
            
    # Clean quotes and unwanted prefixes
    text = text.strip().strip('"').strip("'")
    if text.lower().startswith("pihu:"):
        text = text[5:].strip()
        
    return text if text else "heyy! suno na, kya chal raha hai? ✨"

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
                temperature=0.88,
                max_tokens=180
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
    return "heyy! suno na, kya chal raha hai? ✨"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- Groq AI Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
