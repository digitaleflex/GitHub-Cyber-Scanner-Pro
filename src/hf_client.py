"""Adaptateur backward-compatible — delegue vers src.skills (architecture orientee capacites).

Tous les appels existants (import src.hf_client as hf) continuent de fonctionner
sans modification. Le choix du modele est desormais gere par le registre de capacites.
"""
from src.skills import (
    embed_text,
    embed_batch,
    classify_zero_shot,
    classify_ml,
    extract_entities,
    summarize,
    rerank,
    translate,
    scan_content_safety,
    batch_scan_suspect_repos,
    detect_vuln_type,
    answer_question,
    hf_call as hf_api,
    hf_inference,
    status as hf_status,
    CAPABILITIES as _CAPABILITIES,
)

HF_MODELS = {k: v.get("primary", list(v.values())[0]) for k, v in _CAPABILITIES.items()}
