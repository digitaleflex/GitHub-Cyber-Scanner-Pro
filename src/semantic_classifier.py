import logging
import math
import re
from collections import Counter

logger = logging.getLogger(__name__)

NGRAM_MIN = 3
NGRAM_MAX = 6
TOP_FEATURES = 5000

CATEGORY_DESCRIPTIONS: dict[str, list[str]] = {
    "pentest": [
        "Penetration testing and exploitation framework for security audits",
        "Vulnerability scanning and exploit development toolkit",
        "Red team operations with payload generation and C2 infrastructure",
        "Reverse engineering and binary exploitation tools",
        "SQL injection XSS and web application security testing",
        "Network penetration testing with Metasploit BurpSuite and Nmap",
        "Privilege escalation lateral movement and post exploitation",
        "Fuzzing buffer overflow and zero day exploit development",
    ],
    "defense": [
        "Security incident detection and response platform",
        "SIEM and log analysis for threat hunting and forensics",
        "Endpoint detection and response with behavioral analysis",
        "Network security monitoring with intrusion detection and prevention",
        "Digital forensics malware analysis and memory forensics toolkit",
        "YARA Sigma and Suricata rules for threat detection",
        "Security orchestration automation and response SOAR platform",
    ],
    "cloud": [
        "Cloud security posture management for AWS Azure and GCP",
        "Kubernetes security with container vulnerability scanning",
        "Infrastructure as code security scanning and policy enforcement",
        "Serverless security and DevSecOps pipeline integration",
        "Cloud compliance monitoring and secret detection for repositories",
        "Container runtime security with Falco and Trivy scanning",
        "IAM policy analysis and cloud infrastructure entitlement review",
    ],
    "osint": [
        "Open source intelligence gathering and reconnaissance framework",
        "Social media monitoring and threat intelligence collection",
        "Domain enumeration subdomain discovery and network reconnaissance",
        "Data breach monitoring leaked credential detection and password dump analysis",
        "Geolocation metadata extraction and OSINT automation framework",
        "Shodan Censys search and internet wide scanning data analysis",
    ],
    "mobile": [
        "Mobile application security testing for Android and iOS platforms",
        "Reverse engineering of mobile apps with Frida and Objection",
        "iOS jailbreak detection Android root detection and mobile malware analysis",
        "Mobile API security testing SSL pinning bypass and traffic interception",
    ],
    "iot": [
        "IoT device firmware analysis and embedded security testing",
        "Hardware hacking tools for microcontroller and embedded system security",
        "RFID NFC Bluetooth and Zigbee security testing framework",
        "Industrial control system security SCADA and PLC vulnerability analysis",
        "Firmware extraction binary analysis and hardware debug interface testing",
    ],
    "crypto": [
        "Cryptography library implementing encryption hashing and digital signatures",
        "Blockchain security smart contract auditing and DeFi vulnerability analysis",
        "Zero knowledge proof implementation and cryptographic protocol design",
        "Post quantum cryptography and secure communication protocol library",
        "TLS SSL certificate management PKI infrastructure and secure key storage",
    ],
    "red-team": [
        "Adversary simulation and red team automation framework",
        "Active Directory attack toolkit for domain dominance and privilege escalation",
        "Phishing campaign platform for security awareness testing and simulation",
        "C2 framework for post exploitation lateral movement and data exfiltration",
        "Windows kernel exploitation and advanced persistence technique toolkit",
        "Macro office exploit and initial access vector development",
    ],
    "malware": [
        "Malware source code analysis and reverse engineering of malicious samples",
        "Ransomware analysis decryptor development and ransomware simulation tools",
        "Process injection API hooking and evasion technique implementations",
        "Botnet detection malware traffic analysis and C2 infrastructure tracking",
        "Rootkit detection kernel level security analysis and driver vulnerability research",
        "AMSI bypass ETW patching and Windows defender evasion techniques",
    ],
}


def _char_ngrams(text: str, n_min: int = NGRAM_MIN, n_max: int = NGRAM_MAX) -> list[str]:
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    ngrams = []
    for n in range(n_min, n_max + 1):
        for i in range(len(text) - n + 1):
            ngrams.append(text[i:i + n])
    return ngrams


_built = False
_category_vectors: dict[str, dict[str, float]] = {}
_idf: dict[str, float] = {}
_vocab: list[str] = []


def _build():
    global _built, _category_vectors, _idf, _vocab
    if _built:
        return

    all_docs: list[tuple[str, str]] = []
    for cat, descs in CATEGORY_DESCRIPTIONS.items():
        for desc in descs:
            all_docs.append((cat, desc))

    total = len(all_docs)
    df: Counter[str] = Counter()
    doc_ngrams: list[list[str]] = []

    for _cat, desc in all_docs:
        ngrams = _char_ngrams(desc)
        doc_ngrams.append(ngrams)
        for ng in set(ngrams):
            df[ng] += 1

    top_ngrams = [ng for ng, _ in df.most_common(TOP_FEATURES) if df[ng] >= 1]
    _vocab = top_ngrams

    for ng in _vocab:
        doc_count = df.get(ng, 1)
        _idf[ng] = math.log(total / (doc_count + 1)) + 1

    cat_ngram_map: dict[str, Counter[str]] = {}
    for (_cat, _desc), ngrams in zip(all_docs, doc_ngrams, strict=False):
        if _cat not in cat_ngram_map:
            cat_ngram_map[_cat] = Counter()
        for ng in ngrams:
            if ng in _vocab:
                cat_ngram_map[_cat][ng] += 1

    for cat, counter in cat_ngram_map.items():
        max_freq = max(counter.values()) if counter else 1
        vec: dict[str, float] = {}
        for ng, freq in counter.items():
            tf = 0.5 + 0.5 * (freq / max_freq)
            vec[ng] = tf * _idf.get(ng, 1)
        _category_vectors[cat] = vec

    _built = True
    logger.info("Classification semantique pret: %d categories, %d features", len(_category_vectors), len(_vocab))


def _vectorize(text: str) -> dict[str, float]:
    ngrams = _char_ngrams(text)
    counter = Counter(ng for ng in ngrams if ng in _vocab)
    max_freq = max(counter.values()) if counter else 1
    vec: dict[str, float] = {}
    for ng, freq in counter.items():
        tf = 0.5 + 0.5 * (freq / max_freq)
        vec[ng] = tf * _idf.get(ng, 1)
    return vec


def _cosine_sim(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def classify_semantic(description: str, title: str = "") -> tuple[str, float]:
    _build()
    combined = f"{title} {description}".strip()
    if not combined or combined == " ":
        return "general", 0.0
    vec = _vectorize(combined)
    best_cat = "general"
    best_score = -1.0
    for cat, cat_vec in _category_vectors.items():
        sim = _cosine_sim(vec, cat_vec)
        if sim > best_score:
            best_score = sim
            best_cat = cat
    return best_cat, best_score


def compute_similarity(text1: str, text2: str) -> float:
    _build()
    if not text1 or not text2:
        return 0.0
    v1 = _vectorize(text1)
    v2 = _vectorize(text2)
    return _cosine_sim(v1, v2)


def expand_keywords(seed_keywords: list[str], top_n: int = 20) -> list[tuple[str, float]]:
    _build()
    if not seed_keywords:
        return []
    seed_text = " ".join(seed_keywords)
    seed_vec = _vectorize(seed_text)

    from nlp_processor import CYBER_TERMS

    all_terms = list(set(CYBER_TERMS))
    if not all_terms:
        return []

    scored: list[tuple[str, float]] = []
    for kw in all_terms:
        kw_vec = _vectorize(kw)
        sim = _cosine_sim(seed_vec, kw_vec)
        if sim > 0:
            scored.append((kw, sim))

    scored.sort(key=lambda x: -x[1])
    return scored[:top_n]

