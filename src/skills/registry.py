"""Registre des capacites IA — le choix du modele est un detail, pas du code metier.

Pour ajouter une capacite, un dev ecrit:
    from src.skills import translate
    result = translate("Hello", direction="en_fr")

Pas besoin de connaitre 'Helsinki-NLP/opus-mt-en-fr'.
Le registre selectionne le modele selon la langue, le cout, la latence.
"""

CAPABILITIES = {
    "embedding": {
        "primary": "BAAI/bge-large-en-v1.5",
        "multilingual": "intfloat/multilingual-e5-large",
        "alt": "mixedbread-ai/mxbai-embed-large-v1",
    },
    "classification": {
        "primary": "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7",
        "english_only": "facebook/bart-large-mnli",
    },
    "summarization": {
        "primary": "facebook/bart-large-cnn",
    },
    "reranking": {
        "primary": "mixedbread-ai/mxbai-rerank-large-v1",
        "multilingual": "BAAI/bge-reranker-v2-m3",
    },
    "ner": {
        "primary": "dslim/bert-base-NER",
    },
    "translation": {
        "fr_en": "Helsinki-NLP/opus-mt-fr-en",
        "en_fr": "Helsinki-NLP/opus-mt-en-fr",
    },
    "guard": {
        "primary": "ibm-granite/granite-guardian-hap-125m",
    },
    "vuln_detection": {
        "primary": "jackaduma/SecBERT",
    },
    "qa": {
        "primary": "deepset/roberta-base-squad2",
    },
}


def model_for(capability: str, variant: str = "primary") -> str:
    return CAPABILITIES.get(capability, {}).get(variant, "")
