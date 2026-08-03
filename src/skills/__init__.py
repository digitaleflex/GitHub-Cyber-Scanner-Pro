"""Package skills — capacites IA. Chaque fonction est une capacite, le modele est transparent."""
from .skills import (
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
)
from .core import hf_call, hf_inference, hf_status as status
from .registry import CAPABILITIES, model_for
