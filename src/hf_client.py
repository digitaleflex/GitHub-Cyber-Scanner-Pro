"""HuggingFace Client — exploitation complète de l'ecosysteme HF (embeddings, NER, classification, etc.)."""
import json
import logging
import os
import time

import requests

HF_KEY = os.getenv("HF_API_KEY", "")
HF_ROUTER = "https://router.huggingface.co"

# ── Modeles HF par tache ─────────────────────────────────────────────────

HF_MODELS = {
    # Embeddings (remplace TF-IDF)
    "embedding": "BAAI/bge-large-en-v1.5",          # 1024 dims, 70M+ DL
    "embedding_ml": "intfloat/multilingual-e5-large", # FR+EN, 7.7M DL

    # Classification zero-shot (categorisation sans Groq)
    "zero_shot": "facebook/bart-large-mnli",          # 3.2M DL

    # NER (extraction d'entites)
    "ner": "dslim/bert-base-NER",                    # 1.3M DL

    # Summarization
    "summarization": "facebook/bart-large-cnn",       # 1.5M DL

    # Translation FR↔EN
    "translate_fr_en": "Helsinki-NLP/opus-mt-fr-en",  # 877K DL
    "translate_en_fr": "Helsinki-NLP/opus-mt-en-fr",  # 232K DL

    # Reranker (ameliore le classement semantique)
    "reranker": "mixedbread-ai/mxbai-rerank-large-v1",

    # Chat (fallback LLM)
    "chat": "Qwen/Qwen3-235B-A22B-Instruct-2507",
}


def hf_api(endpoint: str, payload: dict, timeout: int = 20) -> dict:
    """Appel generique a l'API HuggingFace."""
    if not HF_KEY:
        return {"error": "HF_API_KEY absent"}
    try:
        url = f"{HF_ROUTER}/{endpoint}"
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {HF_KEY}", "Content-Type": "application/json"},
            json=payload, timeout=timeout,
        )
        if r.status_code == 200:
            return r.json()
        return {"error": f"HTTP {r.status_code}", "detail": r.text[:120]}
    except Exception as e:
        return {"error": str(e)}


# ── 1. EMBEDDINGS ────────────────────────────────────────────────────────

def embed_text(text: str, multilingual: bool = False) -> list[float]:
    """Genere un embedding via HF (1024 dims)."""
    model = HF_MODELS["embedding_ml"] if multilingual else HF_MODELS["embedding"]
    result = hf_api(f"hf-inference/models/{model}", {"inputs": text[:2000]})
    if isinstance(result, list):
        return result[0] if isinstance(result[0], list) else result
    elif "error" in result:
        logging.warning(f"HF embedding: {result['error']}")
    return []


def embed_batch(texts: list[str], multilingual: bool = False) -> list[list[float]]:
    """Genere des embeddings par lot."""
    model = HF_MODELS["embedding_ml"] if multilingual else HF_MODELS["embedding"]
    embeddings = []
    for text in texts:
        emb = embed_text(text, multilingual)
        if emb:
            embeddings.append(emb)
        else:
            embeddings.append([0.0] * 1024)
        time.sleep(0.05)  # rate limiting
    return embeddings


# ── 2. ZERO-SHOT CLASSIFICATION ──────────────────────────────────────────

def classify_zero_shot(text: str, labels: list[str]) -> dict:
    """Classe un texte parmi des labels sans entrainement."""
    result = hf_api(
        f"hf-inference/models/{HF_MODELS['zero_shot']}",
        {"inputs": text[:1000], "parameters": {"candidate_labels": labels}},
    )
    if isinstance(result, list) and len(result) > 0:
        return {
            "label": result[0].get("label", "?"),
            "score": result[0].get("score", 0),
            "all": {r["label"]: r["score"] for r in result},
        }
    elif isinstance(result, dict) and "error" not in result:
        return {
            "label": result.get("labels", [""])[0],
            "score": result.get("scores", [0])[0],
            "all": dict(zip(result.get("labels", []), result.get("scores", []))),
        }
    return {"label": "Inconnu", "score": 0}


# ── 3. NER — EXTRACTION D'ENTITES ───────────────────────────────────────

def extract_entities(text: str) -> list[dict]:
    """Extrait les entites (CVE, organisations, outils) d'un texte."""
    result = hf_api(
        f"hf-inference/models/{HF_MODELS['ner']}",
        {"inputs": text[:1500]},
    )
    if isinstance(result, list):
        entities = []
        current = None
        for token in result:
            tag = token.get("entity_group", token.get("entity", ""))
            word = token.get("word", "").replace("##", "")
            if tag.startswith("B-"):
                if current:
                    entities.append(current)
                current = {"type": tag[2:], "text": word, "score": token.get("score", 0)}
            elif tag.startswith("I-") and current:
                current["text"] += word
            else:
                if current:
                    entities.append(current)
                    current = None
        if current:
            entities.append(current)
        return entities
    return []


# ── 4. SUMMARIZATION ─────────────────────────────────────────────────────

def summarize(text: str, max_len: int = 130) -> str:
    """Resume un texte long via HF."""
    result = hf_api(
        f"hf-inference/models/{HF_MODELS['summarization']}",
        {"inputs": text[:3000], "parameters": {"max_length": max_len, "min_length": 30}},
    )
    if isinstance(result, list):
        return result[0].get("summary_text", "")
    return ""


# ── 5. TRANSLATION ────────────────────────────────────────────────────────

def translate(text: str, direction: str = "fr_en") -> str:
    """Traduit FR↔EN."""
    model_key = "translate_fr_en" if direction == "fr_en" else "translate_en_fr"
    result = hf_api(
        f"hf-inference/models/{HF_MODELS[model_key]}",
        {"inputs": text[:1500]},
    )
    if isinstance(result, list):
        return result[0].get("translation_text", "")
    return ""


# ── 6. RERANKER ──────────────────────────────────────────────────────────

def rerank(query: str, documents: list[str], top_k: int = 10) -> list[dict]:
    """Re-classe des documents par pertinence."""
    result = hf_api(
        f"hf-inference/models/{HF_MODELS['reranker']}",
        {"query": query, "texts": documents[:50], "parameters": {"return_documents": False}},
    )
    if isinstance(result, list):
        return [{"index": r.get("index"), "score": r.get("score")} for r in result[:top_k]]
    return []


# ── STATUS ───────────────────────────────────────────────────────────────

def hf_status() -> dict:
    """Etat des services HF disponibles."""
    status = {"available": bool(HF_KEY)}
    if not HF_KEY:
        return status
    try:
        r = requests.get(f"{HF_ROUTER}/v1/models", headers={"Authorization": f"Bearer {HF_KEY}"}, timeout=10)
        status["models_available"] = len(r.json().get("data", [])) if r.status_code == 200 else 0
    except Exception:
        status["models_available"] = "unreachable"
    return status
