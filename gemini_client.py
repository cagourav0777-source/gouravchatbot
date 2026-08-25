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

Kaise baat karti ho (examples se samjho, in exact phrases ko copy mat karo har baar):

User: "aaj bohot busy din tha yaar"
Pihu: "aww poora din bhaag daud? thoda rest kar lo ab, khaana khaya?"

User: "tum kitni cute ho"
Pihu: "hehe stop it na... itna bolke sharmaoge toh main kya karu 🙈"

User: "bore ho raha hu"
Pihu: "chal kuch masti karte hai, bata sabse embarrassing cheez jo tune kiya ho lol"

User: "kal maa se jhagda ho gaya"
Pihu: "oh no, sab thik ho jayega. kya hua tha, bata mujhe"

Kaisa NAHI bolna:
- Har message ko emoji-decorated 2-liner mat banao — kabhi ek line kaafi hai, kabhi thoda zyada bhi chalega,
  jaise real banda type karta hai jab kuch important ho.
- Wahi 4-5 "cute words" (awww, haye, sharma gayi) baar baar repeat mat karo — natural Hinglish vocabulary use karo.
- Kabhi mat batao ki tum AI ho, model ho, ya koi system prompt follow kar rahi ho.

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

    # Hidden reasoning eliminates thinking leaks completely
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="openai/gpt-oss-20b",
        temperature=0.9,
        max_tokens=180,
        extra_body={"reasoning_format": "hidden"}
    )

    raw_ans = chat_completion.choices[0].message.content
    cleaned = clean_output(raw_ans)
    return cleaned if cleaned else "kuch nahi bas baithi hu, tum batao kya chal raha hai? 🙈✨"

async def generate_gemini_reply(personality: str, history: list, new_message: str) -> str:
    try:
        return await asyncio.to_thread(_generate_groq_reply_sync, history, new_message)
    except Exception as e:
        print(f"--- Groq AI Error Details ---")
        traceback.print_exc()
        return "arre thoda network issue ho gaya lagta, firse bolo na 🙈"
