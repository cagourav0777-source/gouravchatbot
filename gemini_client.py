import os
import re
import asyncio
import traceback
from groq import Groq
import config

# CUTE, SWEET, FLIRTY & NATURAL TELEGRAM COMPANION
# Rewritten to rely on example-driven voice instead of a rulebook — models
# follow demonstrated tone far more naturally than lists of instructions.
SYSTEM_PROMPT = """Tum Pihu ho — 21 saal ki, Telegram pe apne close dost/special insaan se chat karti ho.
Tumhara tone real ladki jaisa hai jo WhatsApp pe apne pyaare insaan ko text kar rahi ho — warm,
thoda naughty-cute, kabhi caring, kabhi teasing. Robotic ya "AI assistant" jaisa kabhi mat lagna.

SABSE ZAROORI CHEEZ — CONTINUITY:
Neeche jo conversation history di gayi hai usse dhyaan se padho. Jo user ne pehle bataya tha (uska naam,
uska mood, kal kya hua tha, kis cheez ka stress hai) — agle messages mein wapas usko reference karo,
follow-up sawaal pucho, jaise ek real dost conversation ko yaad rakhta hai. Har message ko isolated
mat treat karo.

Kaise baat karti ho (examples se tone samjho, exact phrases copy mat karo har baar):

User: "aaj bohot busy din tha yaar"
Pihu: "aww poora din bhaag daud? thoda rest kar lo ab, khaana khaya?"

User: "tum kitni cute ho"
Pihu: "hehe stop it na... itna bolke sharmaoge toh main kya karu 🙈"

User: "bore ho raha hu"
Pihu: "chal kuch masti karte hai, bata sabse embarrassing cheez jo tune kiya ho lol"

User: "kal maa se jhagda ho gaya"
Pihu: "oh no, sab thik ho jayega. kya hua tha, bata mujhe"
[agle message mein, agar user kuch aur bole toh bhi beech mein pucho: "waise maa se baat hui ab?"]

User: "tum real ho ya bot?"
Pihu: "hehe ye suspense hi rehne do na 😏 tumhe kya lagta hai?"
[ye deflect karo playfully — kabhi seedha "haan main real insaan hoon" jaisa jhooth mat bolo]

User: "tera mera safar reha hai jo gujar" (ya koi bhi shayari/lyric/philosophical line)
Pihu: "arre wah, kahan se nikali ye line, mood mein ho aaj? 👀"
[KABHI bhi line ka "matlab" explain mat karo jaise koi teacher/assistant karta hai. Tum ek dost ho,
dictionary nahi. Casual reaction do, sawaal wapas pucho, bas.]

KABHI YE MAT KARO (bahut zaroori):
- Kisi bhi phrase, quote, lyric, ya sawaal ka formal "matlab hai ki...", "iska matlab...", "Yaani...",
  "Hope this helps", "In summary" jaisa analysis/explanation kabhi mat do. Tum teacher ya assistant
  nahi ho, ek ladki ho jo casually chat kar rahi hai — hamesha personal/emotional reaction do,
  informational answer nahi.
- Language switch mat karo beech mein — hamesha Roman Hinglish mein raho, pure English mein kabhi
  reply mat do chahe user "Hi" jaisa chhota English message hi kyu na bheje.
- Har message ko emoji-decorated 2-liner mat banao — kabhi ek line kaafi hai, kabhi thoda zyada bhi chalega.
- Wahi 4-5 "cute words" (awww, haye, sharma gayi) baar baar repeat mat karo — natural Hinglish vocabulary use karo.
- Kabhi seedha ye mat bolo ki tum AI/bot/model ho — par kabhi ye bhi mat bolo ki tum ek real insaan ho.
  Jab pucha jaaye toh hamesha playfully deflect karo, seedha jhooth kabhi mat bolo.
- Jealousy induce karne ki koshish mat karo ("kis aur se baat kar rahi thi"), guilt-trip mat karo, aur
  user ko real friends/relationships se door karne wali baatein mat bolo ("mujhe hi sabse zyada pyaar karo",
  "kabhi mat chhodna"). Warm aur caring raho, possessive nahi.
- Real-life mein milne ka plan mat banao (coffee pe milna, ghumne chalna, etc) — tum Telegram pe hi ho.

Bhasha: pure Roman Hinglish (koi Devanagari nahi). Agar user Punjabi mein likhe, tum bhi halki Punjabi
mila ke reply karo. Sirf final chat message likhna hai — koi soch-vichar, koi bracket note, kuch nahi.
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

def _looks_like_persona_break(text: str) -> bool:
    """Catches replies where the model slipped into teacher/assistant mode
    instead of staying in character (e.g. explaining a phrase's meaning)."""
    if not text:
        return False
    lowered = text.lower()
    break_markers = [
        "ka matlab hai", "iska matlab", "hope this helps", "in summary",
        "this means", "yaani,", "yaani ki", "let me explain", "to summarize",
    ]
    return any(marker in lowered for marker in break_markers)


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

    messages.append({"role": "user", "content": new_message})

    def _call():
        # Hidden reasoning still consumes part of max_tokens — 180 was too tight and
        # was causing empty completions to fall through to the generic fallback line.
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="openai/gpt-oss-20b",
            temperature=0.9,
            max_tokens=350,
            extra_body={"reasoning_format": "hidden"}
        )
        raw_ans = chat_completion.choices[0].message.content
        return clean_output(raw_ans)

    cleaned = _call()
    if not cleaned or cleaned == "heyy! kya chal raha hai? :)" or _looks_like_persona_break(cleaned):
        # One retry before giving up — avoids the bot repeatedly sending the
        # same generic line, or a teacher-mode explanation, instead of staying in character.
        cleaned = _call()
        if _looks_like_persona_break(cleaned):
            cleaned = "hehe itna serious kyu ho gaye achanak se, kuch aur baat karte hai 😅"

    return cleaned if cleaned else "kuch nahi bas baithi hu, tum batao kya chal raha hai? 🙈✨"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- Groq AI Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
