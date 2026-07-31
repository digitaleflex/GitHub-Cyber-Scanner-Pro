"""LLM Router — fallback intelligent Groq → Gemini → HuggingFace."""
import json
import logging
import os

import requests

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
HF_KEY = os.getenv("HF_API_KEY", "")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
HF_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"


def llm_complete(prompt: str, max_tokens: int = 300, temperature: float = 0.3, timeout: int = 20) -> str:
    """Appelle le LLM avec fallback: Groq → Gemini. Retourne le texte genere."""
    # 1. Groq
    if GROQ_KEY:
        try:
            r = requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile",
                      "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": max_tokens, "temperature": temperature},
                timeout=timeout,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            logging.warning(f"Groq fallback: {r.status_code}")
        except Exception as e:
            logging.warning(f"Groq error: {e}")

    # 2. Gemini
    if GEMINI_KEY:
        try:
            r = requests.post(
                f"{GEMINI_URL}?key={GEMINI_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=timeout,
            )
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            logging.warning(f"Gemini fallback: {r.status_code} {r.text[:100]}")
        except Exception as e:
            logging.warning(f"Gemini error: {e}")

    return ""


def llm_complete_json(prompt: str, max_tokens: int = 400, temperature: float = 0.2, timeout: int = 20) -> dict:
    """Appelle LLM avec fallback et parse le JSON."""
    text = llm_complete(prompt, max_tokens, temperature, timeout)
    if not text:
        return {}
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logging.warning(f"LLM JSON parse error: {text[:100]}")
        return {}
