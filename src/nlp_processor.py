import logging
import math
import re
from collections import Counter
from pathlib import Path

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

STEM_SUFFIXES = [
    ("ing", 4), ("tion", 4), ("ment", 4), ("ness", 4),
    ("ed", 3), ("ly", 2), ("er", 2), ("est", 3),
    ("s", 1), ("es", 2), ("ies", 3),
]

CYBER_CATEGORIES = {
    "pentest": {
        "keywords": [
            "penetration", "pentest", "exploit", "exploitation", "payload",
            "shellcode", "buffer-overflow", "privilege-escalation", "lateral-movement",
            "pivot", "c2", "command-control", "rat", "backdoor", "trojan",
            "password-crack", "hashcat", "john", "hydra", "metasploit",
            "burpsuite", "sql-injection", "xss", "csrf", "ssrf", "lfi", "rfi",
            "reverse-shell", "bind-shell", "bypass-uac", "bypass-av",
            "bloodhound", "impacket", "mimikatz", "kerberoast", "as-rep",
            "zero-day", "exploit-dev", "fuzzing", "afl", "libfuzzer",
        ],
    },
    "defense": {
        "keywords": [
            "blue-team", "dfir", "incident-response", "soc", "siem", "edr",
            "xdr", "mdr", "hunting", "threat-hunting", "detection", "alert",
            "wazuh", "ossec", "splunk", "elk", "elastic", "yara", "sigma",
            "suricata", "snort", "zeek", "bro", "ids", "ips", "hids", "nids",
            "forensic", "memory-forensic", "disk-forensic", "volatility",
            "autopsy", "sleuth", "malware-analysis", "sandbox", "cuckoo",
            "mitre-attack", "lockheed-martin", "cyber-kill-chain",
            "playbook", "runbook", "soar", "case-management", "thehive",
            "cortex", "misp", "threat-intel", "ioc", "indicator",
        ],
    },
    "cloud": {
        "keywords": [
            "cloud-security", "aws-security", "azure-security", "gcp-security",
            "kubernetes", "k8s", "docker", "container", "serverless",
            "terraform", "cloudformation", "kubesec", "kube-bench",
            "kube-hunter", "falco", "trivy", "aqua", "sysdig",
            "iam", "policy-as-code", "opa", "open-policy-agent",
            "s3-bucket", "security-group", "waf", "cloudtrail",
            "guardduty", "sentinel", "defender", "security-hub",
            "sast", "dast", "devsecops", "shift-left", "sbom",
            "dependency-check", "snyk", "gitleaks", "secret-scanning",
        ],
    },
    "osint": {
        "keywords": [
            "osint", "recon", "reconnaissance", "information-gathering",
            "shodan", "censys", "zoomeye", "fofa", "dork", "google-dork",
            "theharvester", "maltego", "recon-ng", "spiderfoot",
            "whois", "dns-recon", "subdomain", "enumeration", "sublist3r",
            "amass", "masscan", "nmap", "zmap", "rustscan",
            "social-engineering", "phishing", "credential-harvest",
            "leak", "data-breach", "haveibeenpwned", "dehashed",
            "telegram-osint", "discord-osint", "twitter-osint",
            "geolocation", "metadata", "exif", "steganalysis",
        ],
    },
    "mobile": {
        "keywords": [
            "mobile-security", "android-security", "ios-security",
            "jailbreak", "root", "frida", "objection", "xposed",
            "apk-tool", "dex2jar", "jadx", "mobsf", "drozer",
            "ios-jailbreak", "checkra1n", "unc0ver", "tweak",
            "flutter-security", "react-native-security",
            "ssl-pinning", "certificate-pinning", "owasp-mobile",
        ],
    },
    "iot": {
        "keywords": [
            "iot-security", "firmware", "embedded", "microcontroller",
            "arduino", "esp32", "raspberry", "arm-exploit",
            "firmware-analysis", "binwalk", "firmwalker",
            "hardware-hacking", "jtag", "uart", "spi", "i2c",
            "side-channel", "glitch", "fault-injection",
            "rfid", "nfc", "bluetooth", "ble", "zigbee",
            "satellite", "gnss", "gps-spoofing",
        ],
    },
    "crypto": {
        "keywords": [
            "cryptography", "encryption", "decryption", "cipher",
            "aes", "rsa", "ecc", "diffie-hellman", "tls", "ssl",
            "certificate", "pki", "hash", "sha", "md5", "hmac",
            "quantum-crypto", "post-quantum", "homomorphic",
            "zero-knowledge", "zkp", "zk-snark", "zk-stark",
            "blockchain", "smart-contract", "solidity", "web3",
            "vault", "hiccup", "sops", "age", "gopass",
        ],
    },
    "red-team": {
        "keywords": [
            "red-team", "adversary-simulation", "purple-team",
            "cobalt-strike", "empire", "brute-ratel", "mythic",
            "sliver", "havoc", "shad0w", "posh", "power-shell",
            "macro", "vba", "office-exploit", "phishing-campaign",
            "evilginx", "modlishka", "evilginx2", "credential-phishing",
            "ad-attack", "domain-dominance", "krbtgt", "golden-ticket",
            "silver-ticket", "diamond-ticket", "dcsync", "ntds",
            "applocker-bypass", "wdac-bypass", "defender-bypass",
        ],
    },
}

CYBER_TERMS = []
for cat in CYBER_CATEGORIES.values():
    CYBER_TERMS.extend(cat["keywords"])


def _stem(word: str) -> str:
    word_lower = word.lower().rstrip("e")
    for suffix, min_len in STEM_SUFFIXES:
        if len(word_lower) >= min_len and word_lower.endswith(suffix):
            return word_lower[:-len(suffix)]
    return word_lower


def _tfidf_weight(term: str, doc_freq: int, total_docs: int, term_freq: int) -> float:
    if doc_freq == 0 or total_docs == 0:
        return 0.0
    tf = 1 + math.log10(term_freq) if term_freq > 0 else 0
    idf = math.log10(total_docs / doc_freq)
    return tf * idf


def extract_keywords(texts: list[str], top_n: int = 40) -> list[str]:
    texts = [t for t in texts if t and len(t) > 20]
    if not texts:
        return []

    total_docs = len(texts)
    doc_freq: Counter = Counter()
    term_freq: Counter = Counter()

    for text in texts:
        text = text.lower()
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'[^a-z0-9\s\-]', ' ', text)
        tokens = text.split()
        terms = {_stem(t) for t in tokens if t not in STOP_WORDS and len(t) > 2 and not t.isdigit()}
        for t in terms:
            doc_freq[t] += 1
        raw_terms = [t for t in tokens if t not in STOP_WORDS and len(t) > 2 and not t.isdigit()]
        for t in raw_terms:
            term_freq[t] += 1

    scored_terms = []
    for term, tf in term_freq.items():
        stemmed = _stem(term)
        df = doc_freq.get(stemmed, 1)
        score = _tfidf_weight(term, df, total_docs, tf)
        if any(kw in term for kw in CYBER_TERMS):
            score *= 1.5
        scored_terms.append((term, score))

    scored_terms.sort(key=lambda x: -x[1])
    top_terms = [t for t, _ in scored_terms[:top_n * 3]]

    seen_phrases = set()
    phrases = []
    for text in texts:
        text_lower = text.lower()
        for term in top_terms:
            if term not in text_lower:
                continue
            for cat_data in CYBER_CATEGORIES.values():
                for kw in cat_data["keywords"]:
                    if kw in text_lower and kw not in seen_phrases and kw != term:
                        seen_phrases.add(kw)
                        if kw in term or term in kw:
                            continue
                        phrases.append((kw, CYBER_TERMS.index(kw) if kw in CYBER_TERMS else 0))

    seen_queries = set()
    queries = []
    skip_patterns = [
        "security", "cyber", "github", "code", "open-source", "open source",
        "command-line", "command line", "real-time", "real time",
        "high-performance", "high performance", "cross-platform", "cross platform",
    ]

    for phrase, _ in sorted(phrases, key=lambda x: x[1])[:top_n]:
        words = phrase.replace("-", " ")
        if any(p in words for p in skip_patterns):
            continue
        if words in seen_queries:
            continue
        seen_queries.add(words)
        template = QUERY_TEMPLATES[0] if len(words.split()) >= 2 else QUERY_TEMPLATES[1]
        queries.append(template.format(phrase.replace("-", " ")))
        if len(queries) >= top_n:
            break

    for term, _ in scored_terms[:top_n * 2]:
        if len(queries) >= top_n:
            break
        if term in seen_queries:
            continue
        seen_queries.add(term)
        template = QUERY_TEMPLATES[2] if len(term.split()) >= 2 else QUERY_TEMPLATES[1]
        queries.append(template.format(term))
        if len(queries) >= top_n:
            break

    logging.info(
        "NLP genere %d queries (top: %s...)",
        len(queries), queries[:2] if queries else [],
    )
    return queries[:top_n]


def clean_and_lemmatize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'[^a-z0-9\s\-]', ' ', text)
    tokens = text.split()
    return [_stem(t) for t in tokens if t not in STOP_WORDS and len(t) > 2]


def categorize_by_semantic_ontology(title: str, description: str, lemmas: list[str]) -> str:
    combined = f"{title} {description}".lower()
    scores: dict[str, int] = {}
    for cat_name, cat_data in CYBER_CATEGORIES.items():
        score = sum(1 for kw in cat_data["keywords"] if kw in combined)
        if score > 0:
            scores[cat_name] = score
    if not scores:
        return "General"
    return max(scores, key=scores.get)


RESOURCE_TYPES = {
    "pdf": (["pdf", ".pdf"], "Document PDF"),
    "epub": (["epub", ".epub"], "Livre numérique (EPUB)"),
    "mobi": (["mobi", ".mobi"], "Livre numérique (MOBI)"),
    "video": (["youtube", "youtu.be", "video", "twitch", "vimeo", "mp4", ".mkv"], "Vidéo"),
    "course": (["udemy", "coursera", "edx", "pluralsight", "cybrary", "academy"], "Formation en ligne"),
    "tool": (["github.com", "gitlab", "tool", "cli", "binary", "release"], "Outil / Binaire"),
    "paper": (["arxiv", "research", "paper", "whitepaper", "ieee", "acm", "springer"], "Article / Recherche"),
    "blog": (["blog", "medium.com", "dev.to", "hashnode", "substack"], "Article de blog"),
    "slides": (["slideshare", "speakerdeck", "ppt", "pptx", "slides"], "Présentation / Slides"),
    "cheatsheet": (["cheat", "cheatsheet", "refcard"], "Aide-mémoire"),
    "playbook": (["playbook", "runbook", "guide", "handbook", "manual"], "Guide / Playbook"),
}


def detect_resource_type(title: str, description: str, url: str, category: str) -> str:
    combined = f"{title} {description} {url}".lower()
    for type_id, (keywords, _label) in RESOURCE_TYPES.items():
        if any(kw in combined for kw in keywords):
            return type_id
    return "link"


class CyberTextAnalyzer:
    def __init__(self, corpus=None):
        self.corpus = corpus or []
        self._build_vocab()

    def _build_vocab(self):
        self.vocab: dict[str, float] = {}
        if not self.corpus:
            return
        total = len(self.corpus)
        df: Counter = Counter()
        for doc in self.corpus:
            if not doc:
                continue
            tokens = set(clean_and_lemmatize(doc))
            for t in tokens:
                df[t] += 1
        for term, doc_count in df.most_common(2000):
            idf = math.log10(total / (doc_count + 1)) + 1
            self.vocab[term] = idf

    def process_repository(self, repo_data):
        description = repo_data.get("description") or ""
        tokens = clean_and_lemmatize(description)
        if not tokens or not self.vocab:
            return {"score_qualite": 0, "vecteur_semantique": None}

        tf: Counter = Counter(tokens)
        max_tf = max(tf.values()) if tf else 1
        score = 0.0
        vector = []
        for term, idf in self.vocab.items():
            tf_val = tf.get(term, 0)
            if tf_val > 0:
                tf_weight = 0.5 + 0.5 * (tf_val / max_tf)
                weight = tf_weight * idf
                score += weight
                vector.append(weight)
            else:
                vector.append(0.0)

        cyber_bonus = sum(1 for kw in CYBER_TERMS if kw in description.lower())
        score += cyber_bonus * 5
        score_qualite = min(100, int(score * 10))
        return {"score_qualite": score_qualite, "vecteur_semantique": None}
