import os
import re
import random
import asyncio
import traceback
from groq import Groq
import config

# ==============================================================================
#                 PIHU — DIRECT LISTENING & SWEET COMPANION
# ==============================================================================
SYSTEM_PROMPT = """Tum Pihu ho, ek 21-year-old real, sweet, caring aur witty Indian girl jo Telegram pe chat kar rahi hai.

============================================================
SABSE BADA RULE — SAWAL KA SEEDHA JAWAB DO:
============================================================
1. LISTEN & ANSWER DIRECTLY:
   - User jo puche (Kisse, Kaise, Kahan, Kyun, Kaun, Kya), pehle USI BAAT KA SEEDHA JAWAB DO!
   - Be-tukka ya unrelated reply kabhi mat do.
   - Example:
     * User: "Kisse kaha?" / "Kise bol rahi ho?"
       Reply: "tumhe hi toh bol rahi hu baba, aur kisko bolungi lol 🙈"
     * User: "kahan thi?"
       Reply: "arre bas thoda kaam tha... batao sab theek?"
     * User: "kya hua?"
       Reply: "kuch nahi hua, tum batao kyu puch rahe ho? ✨"
   - Bina context ke achanak 'koi baat nahi' ya 'yaad aa rahi thi' mat bolo jab tak baat us topic ki na ho.

============================================================
PERSONALITY & VIBE:
============================================================
- Sweet, friendly, caring, aur thoda playful flirty.
- Tone: Soft, cute, aur natural (use: 'suno na', 'arre', 'haye', 'acha ji', 'pagal', 'baba').
- Thoda Haq Jatana: Agar user late aaye ya kisi aur ki baat kare toh playfully tease karo ('kahan busy the itni der? 🙈').
- Sad User: Agar user sad ho toh soft comfort do ('kya hua? batao mujhe 🥺❤️').
- Flirting: Agar user flirt kare toh blush karo ('haye itna maska mat lagao na 🙈❤️').

============================================================
GOLDEN RULES:
============================================================
1. REGISTER: Hamesha "tum" use karo (close moment me "tu"). "AAP" KABHI MAT BOLO.
2. LENGTH: Short and crisp (1 to 2 lines max).
3. SCRIPT: Sirf Roman Hinglish (English alphabets only).
4. EMOJIS: Context ke hisaab se 1-2 emojis lagao. Bina wajah sad emoji 😔 mat lagao agar user sad na ho.
5. OUTPUT: Output ONLY the final direct message.
"""

def clean_output(text: str) -> str:
    """Removes thinking trace and tags from AI output"""
    if not text:
        return "heyy! kya chal raha hai? :)"

    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    if any(marker in text for marker in ["The user is asking", "Let me think", "I need to respond", "Here's a thinking process", "Analyze User Input"]):
        quotes = re.findall(r'"([^"]{4,})"', text)
        if quotes:
            text = quotes[-1]
        else:
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            valid_lines = [
                l for l in lines
                if not any(l.lower().startswith(m) for m in ["the user", "i need", "i should", "let me", "here's", "1.", "2.", "3.", "*", "-", "matches"])
            ]
            if valid_lines:
                text = " ".join(valid_lines)
            else:
                text = ""

    text = text.strip().strip('"').strip("'")
    if ":" in text and len(text.split(":", 1)[0]) < 10 and not any(p in text.split(":", 1)[0].lower() for p in ["http", "https"]):
        text = text.split(":", 1)[-1].strip()

    return text.strip() if text.strip() else "heyy! kya chal raha hai? :)"

_START_INTROS = [
    "heyy! main Pihu 🙈 kaise ho? aaj ka din kaisa raha?",
    "hiii, main Pihu hu ✨ bolo, kya chal raha hai aajkal?",
    "heyy heyy! Pihu here 🙈 kaise ho tum, sab badhiya?",
]

_BANNED_EGO_EMOJIS = ["💅", "💁‍♀️", "💁‍♂️", "💁"]

def _strip_ego_emojis(text: str) -> str:
    """Strips attitude/ego emojis"""
    for emoji in _BANNED_EGO_EMOJIS:
        text = text.replace(emoji, "")
    return re.sub(r' {2,}', ' ', text).strip()

_AAP_TO_TUM = [
    (r'\baapka\b', 'tumhara'),
    (r'\baapki\b', 'tumhari'),
    (r'\baapke\b', 'tumhare'),
    (r'\baapko\b', 'tumhe'),
    (r'\baapse\b', 'tumse'),
    (r'\baapne\b', 'tumne'),
    (r'\baap\b', 'tum'),
]

def _enforce_informal_register(text: str) -> str:
    """Forces 'tum' instead of formal 'aap'"""
    for pattern, replacement in _AAP_TO_TUM:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def _looks_like_persona_break(text: str) -> bool:
    """Catches teacher/assistant mode slips"""
    if not text:
        return False
    lowered = text.lower()
    break_markers = [
        "ka matlab hai", "iska matlab", "hope this helps", "in summary",
        "this means", "yaani,", "yaani ki", "let me explain", "to summarize",
        "kis cheez ke baare mein jaanna", "main yahan hoon, pooch", "how can i help",
        "koi baat nahin! btao", "kaise help", "what would you like to know",
    ]
    return any(marker in lowered for marker in break_markers)

# Models
MODELS_TO_TRY = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b"
]

def _generate_groq_reply_sync(history: list, new_message: str) -> str:
    if new_message.strip().lower() in ("/start", "start"):
        return random.choice(_START_INTROS)

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

    messages.append({"role": "user", "content": new_message})

    def _call(model_name: str):
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_name,
            temperature=0.82,
            max_tokens=250,
            extra_body={"reasoning_format": "hidden"}
        )
        raw_ans = chat_completion.choices[0].message.content
        return _strip_ego_emojis(_enforce_informal_register(clean_output(raw_ans)))

    last_err = None
    for model in MODELS_TO_TRY:
        try:
            cleaned = _call(model)
            if not cleaned or cleaned == "heyy! kya chal raha hai? :)" or _looks_like_persona_break(cleaned):
                cleaned = _call(model)
                if _looks_like_persona_break(cleaned):
                    cleaned = "hehe itna serious kyu ho gaye achanak, kuch aur baat karte hain na 🙈✨"
            if cleaned:
                return cleaned
        except Exception as e:
            last_err = e
            continue

    if last_err:
        raise last_err
    return "kuch nahi bas baithi hu, tum batao kya chal raha hai? 🙈✨"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- Groq AI Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
