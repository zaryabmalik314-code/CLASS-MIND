"""
ClassMind - generation (Groq).

Turns raw extracted slide text into three things per lecture:
- structured notes
- key-point highlights
- a short quiz

Mirrors the primary/fallback model pattern from the LGU Chatbot: try
the strong model first, drop to the fast/small one on rate limits.
"""

import json

from groq import APIStatusError, Groq

import config

PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"

# --- TEMP DEBUG: remove after fixing the 401 ---
print("DEBUG GROQ KEY:", repr(config.GROQ_API_KEY), len(config.GROQ_API_KEY) if config.GROQ_API_KEY else 0)
# --- END TEMP DEBUG ---

SYSTEM_PROMPT = """You are ClassMind, a study assistant that turns raw lecture \
slide text into clean study material for a BS Computing/Mathematics/AI student.

Given the extracted text of a slide deck, produce:
1. "notes": clean, structured notes in markdown (headers per topic, bullet \
points, no fluff, preserve technical accuracy — formulas, definitions, and \
code should stay exact)
2. "highlights": 5-10 key-point bullets, the most exam-relevant facts/concepts
3. "quiz": 5 short quiz questions with answers, testing understanding not \
just recall

Respond with ONLY valid JSON, no markdown fences, no preamble, in this exact \
shape:
{"notes": "...", "highlights": ["...", "..."], "quiz": [{"question": "...", "answer": "..."}]}
"""


def _call_groq(model: str, slide_text: str) -> str:
    client = Groq(api_key=config.GROQ_API_KEY)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Lecture slide text:\n\n{slide_text}"},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content


def generate_lecture_materials(slide_text: str) -> dict:
    """Returns {"notes": str, "highlights": [str], "quiz": [{"question","answer"}]}."""
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set. Add it to .env.")

    try:
        raw = _call_groq(PRIMARY_MODEL, slide_text)
    except APIStatusError as e:
        if e.status_code == 429:  # rate limited — fall back
            raw = _call_groq(FALLBACK_MODEL, slide_text)
        else:
            raise

    # Groq occasionally wraps JSON in fences despite instructions not to.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    return json.loads(cleaned)