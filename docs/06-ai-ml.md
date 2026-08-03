# 06 — AI/ML Architecture

> Module : `src/skills/` · Registre : `src/skills/registry.py`

---

## Philosophie

**Les modèles ne sont pas le produit. Les capacités le sont.**

Un développeur n'a jamais besoin de connaître le nom d'un modèle HuggingFace.
Il appelle `skills.rerank(query, docs)` ou `skills.classify(text, labels)`.
Le registre de capacités choisit le modèle selon le coût, la latence et la langue.

---

## Architecture

```
Code métier (priority_engine, osint_pipeline, api_routes...)
        │
        │  import src.skills
        ▼
┌───────────────────┐
│  Skills Registry  │  ← CAPABILITIES (YAML-like) : quel modèle pour quelle tâche
│  registry.py      │
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│  Skills Engine    │  ← Une fonction par capacité (rerank, classify, embed…)
│  skills.py        │
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│  HF Router         │  ← https://router.huggingface.co
│  core.py           │     (hf_inference, hf_call)
└───────────────────┘

Backward compat : src/hf_client.py → adaptateur transparent
```

---

## Capacités IA

| Capacité | Modèle primaire | Fallback | API |
|----------|----------------|----------|-----|
| Embedding (EN) | BAAI/bge-large-en-v1.5 | mxbai-embed-large-v1 | `embed_text()` |
| Embedding (FR+EN) | intfloat/multilingual-e5-large | — | `embed_text(ml=True)` |
| Classification (FR+EN) | mDeBERTa-v3-base-xnli | bart-large-mnli | `classify_ml()` |
| Classification (EN) | facebook/bart-large-mnli | — | `classify_zero_shot()` |
| Reranking (EN) | mxbai-rerank-large-v1 | — | `rerank()` |
| Reranking (FR+EN) | BAAI/bge-reranker-v2-m3 | — | `rerank(ml=True)` |
| Summarization | facebook/bart-large-cnn | — | `summarize()` |
| NER | dslim/bert-base-NER | — | `extract_entities()` |
| Traduction FR→EN | Helsinki-NLP/opus-mt-fr-en | — | `translate(dir="fr_en")` |
| Traduction EN→FR | Helsinki-NLP/opus-mt-en-fr | — | `translate(dir="en_fr")` |
| Guardrails | granite-guardian-hap-125m | — | `scan_content_safety()` |
| Vuln Detection | jackaduma/SecBERT | — | `detect_vuln_type()` |
| QA | deepset/roberta-base-squad2 | — | `answer_question()` |

---

## Ajouter une capacité

1. Ajouter une entrée dans `CAPABILITIES` (registry.py) avec modèle primaire + fallback
2. Créer une fonction dans `skills.py` utilisant `hf_inference(model, payload)`
3. Exporter dans `__init__.py`
4. Mettre à jour `hf_client.py` si rétrocompatibilité requise

Exemple pour ajouter un nouveau reranker :
```python
# registry.py
CAPABILITIES["reranking"]["fast"] = "sentence-transformers/all-MiniLM-L6-v2"

# skills.py
def rerank_fast(query, documents):
    model = model_for("reranking", "fast")
    return hf_inference(model, {"query": query, "texts": documents})
```

---

## LLM Router (analyse CVE)

Pour les tâches nécessitant un LLM (explication de CVE, génération de rapport),
le projet utilise le **router HuggingFace** (`https://router.huggingface.co/v1/chat/completions`)
via `src/llm_router.py`. Le modèle utilisé (`Qwen/Qwen3-235B-A22B-Instruct-2507`)
est défini dans le registre HF_MODELS mais n'est pas encore utilisé via l'API skills.

Alternatives disponibles (via variables d'environnement) :
- `GROQ_API_KEY` → Groq (LLaMA)
- `GEMINI_API_KEY` → Google Gemini
