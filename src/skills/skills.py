"""Skills IA — une fonction par capacite. Le modele est choisi par le registre, pas par l'appelant."""
import logging
import time

from .core import hf_inference, hf_call
from .registry import model_for


def embed_text(text: str, multilingual: bool = False) -> list[float]:
    model = model_for("embedding", "multilingual" if multilingual else "primary")
    result = hf_inference(model, {"inputs": text[:2000]})
    if isinstance(result, list):
        return result[0] if isinstance(result[0], list) else result
    if isinstance(result, dict) and "error" in result:
        logging.warning(f"Skills/embed: {result['error']}")
    return []


def embed_batch(texts: list[str], multilingual: bool = False) -> list[list[float]]:
    embeddings = []
    for text in texts:
        emb = embed_text(text, multilingual)
        embeddings.append(emb if emb else [0.0] * 1024)
        time.sleep(0.05)
    return embeddings


def classify_zero_shot(text: str, labels: list[str]) -> dict:
    model = model_for("classification", "english_only")
    result = hf_inference(
        model,
        {"inputs": text[:1000], "parameters": {"candidate_labels": labels}},
    )
    if isinstance(result, list) and len(result) > 0:
        return {
            "label": result[0].get("label", "?"),
            "score": result[0].get("score", 0),
            "all": {r["label"]: r["score"] for r in result},
        }
    if isinstance(result, dict) and "error" not in result:
        return {
            "label": result.get("labels", [""])[0],
            "score": result.get("scores", [0])[0],
            "all": dict(zip(result.get("labels", []), result.get("scores", []), strict=False)),
        }
    return {"label": "Inconnu", "score": 0}


def classify_ml(text: str, labels: list[str]) -> dict:
    model = model_for("classification", "primary")
    result = hf_inference(
        model,
        {"inputs": text[:1000], "parameters": {"candidate_labels": labels}},
    )
    if isinstance(result, list) and len(result) > 0:
        return {
            "label": result[0].get("label", "?"),
            "score": result[0].get("score", 0),
            "all": {r["label"]: r["score"] for r in result},
        }
    return {"label": "Inconnu", "score": 0}


def extract_entities(text: str) -> list[dict]:
    model = model_for("ner", "primary")
    result = hf_inference(model, {"inputs": text[:1500]})
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


def summarize(text: str, max_len: int = 130) -> str:
    model = model_for("summarization", "primary")
    result = hf_inference(
        model,
        {"inputs": text[:3000], "parameters": {"max_length": max_len, "min_length": 30}},
    )
    if isinstance(result, list):
        return result[0].get("summary_text", "")
    return ""


def rerank(query: str, documents: list[str], top_k: int = 10, multilingual: bool = False) -> list[dict]:
    model = model_for("reranking", "multilingual" if multilingual else "primary")
    result = hf_inference(
        model,
        {
            "query": query,
            "texts": documents[:50],
            "parameters": {"return_documents": False},
        },
    )
    if isinstance(result, list):
        return [{"index": r.get("index"), "score": r.get("score")} for r in result[:top_k]]
    return []


def translate(text: str, direction: str = "fr_en") -> str:
    model = model_for("translation", direction)
    if not model:
        return text
    result = hf_inference(model, {"inputs": text[:1500]})
    if isinstance(result, list):
        return result[0].get("translation_text", "")
    return ""


def scan_content_safety(text: str) -> dict:
    model = model_for("guard", "primary")
    result = hf_inference(model, {"inputs": text[:1000]})
    if isinstance(result, list):
        return {"flagged": True, "raw": result}
    return {"flagged": False}


def batch_scan_suspect_repos(limit: int = 20) -> int:
    from src.database import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, full_name, description FROM repositories
        WHERE security_verdict IN ('Suspect', 'Critique')
          AND description IS NOT NULL
        ORDER BY stars DESC LIMIT %s
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    flagged = 0
    for repo_id, name, desc in rows:
        r = scan_content_safety(desc or name)
        if r["flagged"]:
            cursor.execute(
                "UPDATE repositories SET ai_category = 'Content Flagged' WHERE id = %s",
                (repo_id,),
            )
            flagged += 1
    conn.commit()
    cursor.close()
    conn.close()
    return flagged


def detect_vuln_type(text: str) -> str:
    model = model_for("vuln_detection", "primary")
    masked = text + " [MASK]"
    result = hf_inference(model, {"inputs": masked[:500]})
    if isinstance(result, list) and len(result) > 0:
        return result[0].get("token_str", result[0].get("sequence", ""))
    return ""


def answer_question(question: str, context: str) -> str:
    model = model_for("qa", "primary")
    result = hf_inference(
        model,
        {"inputs": {"question": question, "context": context[:2000]}},
    )
    if isinstance(result, dict):
        return result.get("answer", "")
    return ""
