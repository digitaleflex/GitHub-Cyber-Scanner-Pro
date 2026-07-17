import logging
import math
import re
from collections import Counter
from typing import Iterable

from semantic_classifier import classify_semantic, CATEGORY_DESCRIPTIONS

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "for", "of", "to", "in", "on", "at", "by", "with", "from", "as", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "cannot", "must", "shall", "not", "no", "yes", "so", "if", "then",
    "than", "that", "this", "these", "those", "it", "its", "he", "she", "him", "her", "his", "they", "them",
    "their", "we", "us", "our", "you", "your", "my", "me", "i", "am", "who", "what", "which", "where", "when",
    "why", "how", "all", "any", "some", "many", "much", "few", "more", "most", "other", "another", "such", "only",
    "own", "same", "each", "every", "both", "either", "neither", "one", "two", "three", "first", "last", "new",
    "old", "good", "bad", "big", "small", "long", "short", "high", "low", "right", "left", "here", "there", "now",
    "then", "today", "tomorrow", "yesterday", "way", "just", "also", "too", "very", "quite", "rather", "still",
    "yet", "already", "almost", "even", "only", "about", "above", "across", "after", "against", "along", "among",
    "around", "before", "behind", "below", "beneath", "beside", "between", "beyond", "during", "inside", "into",
    "near", "off", "onto", "out", "outside", "over", "through", "throughout", "till", "toward", "under", "until",
    "up", "upon", "within", "without", "via", "using", "based", "tool", "tools", "library", "libraries", "framework",
    "platform", "application", "app", "software", "program", "project", "simple", "easy", "fast", "lightweight",
    "written", "built", "made", "provides", "allows", "supports", "includes", "used", "use", "using", "useful",
    "set", "collection", "list", "script", "cli", "gui", "implementation", "implement", "source", "code",
    "open", "repository", "repo", "github", "gitlab", "version", "latest", "release", "update", "updated",
    "create", "created", "creates", "creating", "make", "making", "made", "build", "building", "designed", "based",
    "help", "helps", "helping", "used", "using", "designed", "used", "allow", "allows", "allowing", "enable",
    "enables", "support", "supports", "supporting", "include", "includes", "including", "provide", "provides",
    "providing", "contain", "contains", "containing", "feature", "features", "based", "powered", "fork", "mirror",
    "clone", "download", "install", "setup", "configure", "configuration", "config", "documentation", "docs",
    "guide", "tutorial", "example", "examples", "sample", "samples", "template", "templates", "test", "tests",
    "testing", "benchmark", "benchmarks", "demo", "demos", "showcase", "resource", "resources", "reference",
    "awesome", "curated", "collection", "list", "lists", "repository", "repositories", "database", "dataset",
    "data", "files", "file", "folder", "directory", "path", "paths", "url", "link", "links", "page", "pages",
    "website", "web", "site", "online", "api", "apis", "json", "xml", "yaml", "csv", "format", "formats", "html",
    "css", "javascript", "js", "typescript", "ts", "python", "java", "go", "golang", "rust", "cpp", "c", "csharp",
    "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "shell", "bash", "powershell", "sql", "perl",
    "linux", "windows", "macos", "mac", "unix", "ubuntu", "debian", "centos", "redhat", "fedora", "android",
    "ios", "mobile", "desktop", "server", "client", "frontend", "backend", "fullstack", "webapp", "webapps",
}

SKIP_PATTERNS = {
    "http", "https", "www", "com", "org", "net", "io", "dev", "github", "gitlab", "npm", "pypi",
    "install", "readme", "license", "changelog", "contributing", "dockerfile", "requirements", "package",
    "copyright", "author", "authors", "maintainer", "email", "twitter", "linkedin", "discord", "telegram",
    "build passing", "codecov", "travis", "circleci", "github actions", "dependabot", "snyk", "badge",
}

NGRAM_RANGES = [(1, 1), (2, 2), (3, 3)]


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'[^a-z0-9\- ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.split()


def _extract_ngrams(tokens: list[str]) -> list[str]:
    ngrams = []
    for n_min, n_max in NGRAM_RANGES:
        for n in range(n_min, n_max + 1):
            for i in range(len(tokens) - n + 1):
                ngrams.append(" ".join(tokens[i:i + n]))
    return ngrams


def _is_valid_term(term: str) -> bool:
    if len(term) < 3 or len(term) > 60:
        return False
    if any(p in term for p in SKIP_PATTERNS):
        return False
    words = term.split()
    if all(w in STOP_WORDS for w in words):
        return False
    if any(w in STOP_WORDS for w in words) and len(words) == 1:
        return False
    if re.search(r'\d{4,}', term):
        return False
    return True


def _score_term(
    term: str,
    doc_freq: Counter,
    term_freq: Counter,
    total_docs: int,
    cyber_doc_freq: Counter,
    cyber_total: int,
) -> float:
    tf = term_freq.get(term, 0)
    df = doc_freq.get(term, 1)

    # Hard filters
    if df < 3:
        return 0.0
    if df > total_docs * 0.15:
        return 0.0

    idf = math.log((total_docs + 1) / (df + 1)) + 1
    tf_weight = 1 + math.log1p(tf)
    cyber_df = cyber_doc_freq.get(term, 0)
    cyber_ratio = (cyber_df + 1) / (cyber_total + 1) if cyber_total > 0 else 0

    # Single-word terms must be strongly cyber-related
    if " " not in term and cyber_df < 3:
        return 0.0

    specificity = idf * (1 + cyber_ratio)
    score = tf_weight * specificity

    security_hints = [
        "sec", "hack", "exploit", "vuln", "threat", "malware", "ransomware",
        "pentest", "forensic", "crypto", "phishing", "botnet", "c2", "shell",
        "injection", "bypass", "recon", "osint", "siem", "kubernetes", "container",
        "ransom", "trojan", "rat ", "keylogger", "rootkit", "backdoor", "payload",
        "privilege", "escalation", "lateral", "movement", "persistence", "credential",
        "brute", "force", "dictionary", "fuzz", "reverse", "engineering", "analysis",
    ]
    if any(h in term for h in security_hints):
        score *= 1.5

    # Penalize overly generic terms
    if df > total_docs * 0.05:
        score *= 0.5

    return score


def _guess_category(term: str, sample_texts: list[str]) -> str | None:
    combined = " ".join(sample_texts[:3])
    cat, score = classify_semantic(combined, term)
    if score > 0.25:
        return cat
    return None


def mine_keywords(
    repo_descriptions: Iterable[str],
    news_texts: Iterable[str] | None = None,
    top_n: int = 200,
) -> list[dict]:
    """
    Mine des mots-clés candidats depuis les descriptions de repos et les news.
    Retourne une liste de dicts prêts pour `database.save_discovered_keywords`.
    """
    descriptions = [d for d in repo_descriptions if d and len(d) > 10]
    news = [n for n in (news_texts or []) if n and len(n) > 10]
    total_docs = len(descriptions)
    if total_docs < 10:
        logger.info("Keyword miner: pas assez de documents (%d)", total_docs)
        return []

    doc_freq: Counter = Counter()
    term_freq: Counter = Counter()
    term_sources: dict[str, set[str]] = {}

    cyber_doc_freq: Counter = Counter()
    cyber_total = 0

    for desc in descriptions:
        tokens = _tokenize(desc)
        ngrams = _extract_ngrams(tokens)
        seen = set()
        for ng in ngrams:
            if not _is_valid_term(ng):
                continue
            term_freq[ng] += 1
            if ng not in seen:
                seen.add(ng)
                doc_freq[ng] += 1
                term_sources.setdefault(ng, set()).add("repo")

        # Cyber docs = those semantically close to a cyber category
        sem_cat, sem_score = classify_semantic(desc)
        if sem_score > 0.25:
            cyber_total += 1
            for ng in seen:
                cyber_doc_freq[ng] += 1

    for text in news:
        tokens = _tokenize(text)
        ngrams = _extract_ngrams(tokens)
        seen = set()
        for ng in ngrams:
            if not _is_valid_term(ng):
                continue
            if ng not in seen:
                seen.add(ng)
                term_sources.setdefault(ng, set()).add("news")

    candidates = []
    for term in term_freq:
        if not _is_valid_term(term):
            continue
        score = _score_term(term, doc_freq, term_freq, total_docs, cyber_doc_freq, cyber_total)
        if score <= 0:
            continue
        sources = len(term_sources.get(term, set()))
        # Bonus for appearing in multiple source types
        score *= (1 + 0.2 * sources)
        candidates.append((term, score, sources))

    candidates.sort(key=lambda x: -x[1])

    results = []
    seen_terms = set()
    for term, score, sources in candidates:
        if term in seen_terms:
            continue
        # Skip if term is a substring of an already selected longer term
        if any(t != term and term in t for t in seen_terms):
            continue
        seen_terms.add(term)

        samples = []
        for desc in descriptions:
            if term in desc.lower():
                samples.append(desc[:120])
                if len(samples) >= 3:
                    break

        category_guess = _guess_category(term, samples)
        results.append({
            "term": term,
            "category_guess": category_guess,
            "score": round(score, 4),
            "sources": sources,
            "source_samples": " | ".join(samples),
        })
        if len(results) >= top_n:
            break

    logger.info("Keyword miner: %d candidats extraits", len(results))
    return results


def enrich_static_keywords() -> list[str]:
    """Retourne la liste des mots-clés approuvés pour enrichir CYBER_TERMS."""
    from database import get_approved_keywords
    return [kw["term"] for kw in get_approved_keywords()]
