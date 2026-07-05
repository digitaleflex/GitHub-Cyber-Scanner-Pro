import logging
import re
from collections import Counter
from typing import List, Optional

STOP_WORDS = {
    "a", "an", "the", "and", "or", "for", "of", "to", "in", "on", "at",
    "with", "by", "from", "as", "is", "it", "its", "this", "that", "was",
    "are", "been", "be", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "just", "about",
    "above", "after", "again", "against", "below", "between", "during",
    "before", "behind", "off", "over", "through", "under", "up", "down",
    "out", "into", "onto", "upon", "via", "using", "based", "built",
    "tool", "tools", "library", "libraries", "framework", "platform",
    "simple", "easy", "fast", "lightweight", "yet", "also", "well",
    "set", "collection", "list", "project", "script", "cli", "gui",
    "implementation", "implement", "written", "made", "provides",
    "supports", "includes", "allows", "used", "use", "new", "one"
}

QUERY_TEMPLATES = [
    '"{}" cybersecurity',
    '"{}" security',
    '"{}" hacking',
    '"{}" tools',
    '"{}" awesome',
    '"{}" framework',
]


def extract_keywords(texts: List[str], top_n: int = 40) -> List[str]:
    texts = [t for t in texts if t and len(t) > 20]
    if not texts:
        return []

    phrases: Counter = Counter()

    for text in texts:
        text = text.lower()
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'[^a-z0-9\s\-]', ' ', text)
        tokens = text.split()
        terms = [t for t in tokens if t not in STOP_WORDS and len(t) > 2 and not t.isdigit()]

        for i in range(len(terms)):
            if i + 1 < len(terms):
                bigram = f"{terms[i]}-{terms[i+1]}"
                if len(terms[i]) >= 3 and len(terms[i+1]) >= 3:
                    phrases[bigram] += 1
            if i + 2 < len(terms):
                trigram = f"{terms[i]}-{terms[i+1]}-{terms[i+2]}"
                if len(terms[i]) >= 3 and len(terms[i+1]) >= 3 and len(terms[i+2]) >= 3:
                    phrases[trigram] += 1

    min_freq = max(2, len(texts) // 100)
    candidates = [(p, f) for p, f in phrases.most_common(top_n * 3) if f >= min_freq]
    if not candidates:
        return []

    skip_patterns = [
        "security", "cyber", "github", "code", "open-source", "open source",
        "command-line", "command line", "real-time", "real time",
        "high-performance", "high performance", "cross-platform", "cross platform"
    ]

    seen_queries = set()
    queries = []
    for phrase, _ in candidates:
        words = phrase.replace('-', ' ')
        if any(p in words for p in skip_patterns):
            continue
        if words in seen_queries:
            continue
        seen_queries.add(words)
        template = QUERY_TEMPLATES[0] if len(words.split()) >= 2 else QUERY_TEMPLATES[1]
        queries.append(template.format(phrase.replace('-', ' ')))
        if len(queries) >= top_n:
            break

    logging.info(f"🧠 NLP généré {len(queries)} nouvelles queries: {queries[:3]}...")
    return queries


# Backward-compatible stubs for scanner.py
def clean_and_lemmatize(text: str) -> List[str]:
    return text.lower().split()


def categorize_by_semantic_ontology(title: str, description: str, lemmas: List[str]) -> str:
    return "General"


def detect_resource_type(title: str, description: str, url: str, category: str) -> str:
    return "link"


class CyberTextAnalyzer:
    def __init__(self, corpus=None):
        self.corpus = corpus or []

    def process_repository(self, repo_data):
        return {"score_qualite": 0, "vecteur_semantique": None}

    def clean_and_lemmatize(self, text):
        return text.lower().split()

    def categorize_by_semantic_ontology(self, title, description, lemmas):
        return "General"

    def detect_resource_type(self, title, description, url, category):
        return "link"
