"""Semantic embeddings for repositories (TF-IDF + SVD, stocke dans pgvector)."""
import logging
import os
import pickle
import re

import numpy as np

VECTOR_DIM = 384
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tfidf_svd.pkl")
_vectorizer = None
_svd = None
_idf = None  # mean idf pour textes hors-vocabulaire


def _preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-_+#.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_or_load_model():
    """Construit TF-IDF + SVD depuis les descriptions existantes, ou charge depuis le cache."""
    global _vectorizer, _svd, _idf
    if _vectorizer is not None:
        return

    if os.path.exists(_MODEL_PATH):
        with open(_MODEL_PATH, "rb") as f:
            data = pickle.load(f)
        _vectorizer = data["vectorizer"]
        _svd = data["svd"]
        _idf = data.get("idf", 0.0)
        logging.info(f"Modele TF-IDF/SVD charge ({_svd.n_components} dims)")
        return

    from src.database import get_db_connection
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT description FROM repositories WHERE description IS NOT NULL AND description != ''")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        _vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        _vectorizer.fit(["placeholder"])
        _svd = TruncatedSVD(n_components=VECTOR_DIM)
        return

    texts = [_preprocess(r[0]) for r in rows]
    logging.info(f"Construction TF-IDF sur {len(texts)} descriptions...")
    _vectorizer = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), sublinear_tf=True)
    X = _vectorizer.fit_transform(texts)
    _idf = float(np.mean(_vectorizer.idf_))

    n_comp = min(VECTOR_DIM, X.shape[1] - 1, X.shape[0] - 1)
    if n_comp < 2:
        _svd = None
        return

    logging.info(f"SVD: {X.shape[1]} features → {n_comp} composants")
    _svd = TruncatedSVD(n_components=n_comp, random_state=42)
    _svd.fit(X)

    with open(_MODEL_PATH, "wb") as f:
        pickle.dump({"vectorizer": _vectorizer, "svd": _svd, "idf": _idf}, f)
    logging.info(f"Modele TF-IDF/SVD sauvegarde → {_MODEL_PATH}")


def embed_text(text: str) -> list[float]:
    _build_or_load_model()
    clean = _preprocess(text)
    X = _vectorizer.transform([clean])
    if _svd is not None:
        vec = _svd.transform(X)[0]
        return vec.tolist()
    return _pad_or_truncate(X.toarray()[0], VECTOR_DIM)


def embed_batch(texts: list[str]) -> list[list[float]]:
    _build_or_load_model()
    clean = [_preprocess(t) for t in texts]
    X = _vectorizer.transform(clean)
    if _svd is not None:
        vecs = _svd.transform(X)
        return [v.tolist() for v in vecs]
    return [_pad_or_truncate(X[i].toarray()[0], VECTOR_DIM) for i in range(X.shape[0])]


def _pad_or_truncate(arr: np.ndarray, target_dim: int) -> list[float]:
    vec = arr.tolist()
    if len(vec) > target_dim:
        return vec[:target_dim]
    return vec + [0.0] * (target_dim - len(vec))


def embed_unembedded_repos(limit: int = 200) -> int:
    from src.database import get_db_connection

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, description FROM repositories
               WHERE embedding IS NULL AND description IS NOT NULL AND description != ''
               ORDER BY stars DESC NULLS LAST LIMIT %s""",
            (limit,),
        )
        rows = cursor.fetchall()
        if not rows:
            cursor.close()
            conn.close()
            return 0

        ids = [r[0] for r in rows]
        texts = [r[1] or "" for r in rows]
        embeddings = embed_batch(texts)

        for rid, emb in zip(ids, embeddings, strict=False):
            cursor.execute(
                "UPDATE repositories SET embedding = %s WHERE id = %s",
                (emb, rid),
            )
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"🧬 Embeddings generes pour {len(rows)} depot(s)")
        return len(rows)
    except Exception as e:
        logging.error(f"Erreur embed_unembedded_repos: {e}")
        return 0


def semantic_search(query: str, limit: int = 20, min_score: float = 0.15) -> list[dict]:
    from src.database import get_db_connection
    from psycopg2.extras import RealDictCursor

    query_embedding = embed_text(query)
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT full_name AS name, description AS desc, stars, language AS lang,
                   html_url AS url, security_verdict,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM repositories
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, query_embedding, limit))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows if r.get("similarity", 0) >= min_score]
    except Exception as e:
        logging.error(f"Erreur semantic_search: {e}")
        return []


def embedding_status() -> dict:
    from src.database import get_db_connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM repositories WHERE embedding IS NOT NULL")
        with_emb = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM repositories")
        total = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"with_embedding": with_emb, "total": total, "percent": round(with_emb / total * 100, 1) if total else 0}
    except Exception as e:
        return {"error": str(e)}
