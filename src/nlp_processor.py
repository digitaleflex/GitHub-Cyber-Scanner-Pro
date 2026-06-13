import logging
import re

import spacy
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Modèle d'Embedding ultra-léger et ultra-performant pour CPU/Docker (dimension 384)
encoder = None

# Modèles Spacy chargés de manière paresseuse
_nlp_en = None
_nlp_fr = None

# Dictionnaire de référence pour repérer les concepts de confiance cyber
CYBER_PATTERNS = [
    r"remote code execution",
    r"privilege escalation",
    r"active directory",
    r"buffer overflow",
    r"reverse engineering",
    r"threat hunting",
    r"malware analysis",
    r"zero day",
    r"credential stuffing",
    r"command and control",
]

# Matrice sémantique historique pour catégorisation
CYBER_ONTOLOGY = {
    "offensive": [
        "pentest", "exploit", "red team", "payload", "fuzzing", "bypass", "malware",
        "hack", "pwn", "sqli", "buffer overflow", "reversing"
    ],
    "defensive": [
        "blue team", "hardening", "soc", "siem", "edr", "dfir", "forensics",
        "incident response", "detection", "yara"
    ],
    "application_security": [
        "appsec", "owasp", "code audit", "vulnerability", "web security", "devsecops",
        "secure coding"
    ],
    "governance": [
        "iso27001", "rgpd", "gdpr", "ebios", "risk assessment", "compliance", "audit"
    ]
}

def get_encoder():
    """Charge paresseusement le modèle d'embeddings SentenceTransformers."""
    global encoder
    if encoder is None:
        try:
            encoder = SentenceTransformer("all-MiniLM-L6-v2")
            logging.info("🧠 Modèle SentenceTransformer (all-MiniLM-L6-v2) chargé avec succès.")
        except Exception as e:
            logging.error(f"❌ Impossible de charger SentenceTransformer : {e}")
    return encoder

def get_nlp_models():
    """Charge paresseusement les modèles linguistiques de Spacy."""
    global _nlp_en, _nlp_fr

    if _nlp_en is None:
        try:
            _nlp_en = spacy.load("en_core_web_sm")
            logging.info("🧠 Modèle Spacy anglais (en_core_web_sm) chargé avec succès.")
        except OSError:
            logging.warning("⚠️ Impossible de charger 'en_core_web_sm'. Fallback minimal.")
            _nlp_en = spacy.blank("en")

    if _nlp_fr is None:
        try:
            _nlp_fr = spacy.load("fr_core_news_sm")
            logging.info("🧠 Modèle Spacy français (fr_core_news_sm) chargé avec succès.")
        except OSError:
            logging.warning("⚠️ Impossible de charger 'fr_core_news_sm'. Fallback minimal.")
            _nlp_fr = spacy.blank("fr")

    return _nlp_en, _nlp_fr


def detect_language(text):
    if not text:
        return "en"
    text_lower = text.lower()
    fr_markers = {"le", "la", "les", "des", "pour", "dans", "avec", "est", "une", "sécurité", "livre"}
    en_markers = {"the", "and", "for", "with", "book", "security", "this", "from", "hacking"}

    words = set(re.findall(r'[a-zÀ-ÿ]+', text_lower))
    fr_count = len(words.intersection(fr_markers))
    en_count = len(words.intersection(en_markers))
    return "fr" if fr_count > en_count else "en"


class CyberTextAnalyzer:
    def __init__(self, corpus_descriptions=None):
        """Initialise l'analyseur avec un corpus optionnel pour l'algorithme TF-IDF."""
        self.corpus = corpus_descriptions if corpus_descriptions else []
        self.tfidf = TfidfVectorizer(
            stop_words="english", max_features=500, ngram_range=(1, 2)
        )
        if len(self.corpus) > 0:
            try:
                self.tfidf.fit(self.corpus)
            except Exception as e:
                logging.warning(f"⚠️ Impossible d'ajuster le TF-IDF : {e}")

    def extract_key_phrases(self, text):
        """Extrait les phrases et concepts clés (Noun Chunks) les plus pertinents techniquement."""
        if not text:
            return []

        lang = detect_language(text)
        nlp_en, nlp_fr = get_nlp_models()
        nlp_model = nlp_fr if lang == "fr" else nlp_en

        doc = nlp_model(text.lower())
        key_phrases = []

        # 1. Extraction par grammaire (groupes nominaux nettoyés)
        for chunk in doc.noun_chunks:
            clean_tokens = [token.lemma_ for token in chunk if not token.is_stop and not token.is_punct and not token.is_space]
            clean_chunk = " ".join(clean_tokens)
            if len(clean_chunk.split()) >= 1 and len(clean_chunk) > 2:
                key_phrases.append(clean_chunk)

        # 2. Extraction par expressions régulières (Regex) sur le jargon cyber d'autorité
        for pattern in CYBER_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                key_phrases.append(pattern)

        return list(set(key_phrases))

    def calculate_relevance_score(self, repo_data, key_phrases):
        """Calcule une note de pertinence et de qualité sur 100 pour identifier les pépites."""
        score = 0
        description = repo_data.get("description", "")
        description_lower = description.lower() if description else ""
        stars = int(repo_data.get("stars", repo_data.get("stargazers_count", 0)))

        # RÈGLE 1 : Richesse sémantique (quantité de concepts techniques)
        score += min(len(key_phrases) * 15, 45)

        # RÈGLE 2 : Bonus pour les termes d'autorité cyber
        for pattern in CYBER_PATTERNS:
            if re.search(pattern, description_lower):
                score += 15

        # RÈGLE 3 : Popularité logarithmique modérée (ne pas écraser les petits projets très techniques)
        if stars > 0:
            import math
            score += min(math.log2(stars) * 2, 20)

        # RÈGLE 4 : Pénalités de pollution (spam, crypto, etc.)
        spam_keywords = ["crypto currency", "airdrop", "forex", "make money", "crypto", "trading"]
        for spam in spam_keywords:
            if spam in description_lower:
                score -= 40

        return min(max(int(score), 0), 100)

    def process_repository(self, repo_data):
        """Analyse sémantique complète d'un dépôt (phrases clés, embeddings vectoriels, score de qualité)."""
        description = repo_data.get("description", "")
        title = repo_data.get("full_name", "")

        # Concaténer le titre et la description
        text_to_analyze = f"{title} {description if description else ''}"

        # 1. Mots-clés et phrases clés
        keywords = self.extract_key_phrases(text_to_analyze)

        # 2. Calcul du vecteur sémantique (Embedding 384 dimensions)
        vector = []
        model = get_encoder()
        if model is not None and description:
            try:
                vector = model.encode(description).tolist()
            except Exception as e:
                logging.error(f"❌ Erreur de génération de l'embedding : {e}")

        # 3. Calcul du score de qualité
        quality_score = self.calculate_relevance_score(repo_data, keywords)

        return {
            "mots_cles": keywords,
            "vecteur_semantique": vector,
            "score_qualite": quality_score
        }


def clean_and_lemmatize(text):
    """Méthode de nettoyage et de lemmatisation générique (conservée pour compatibilité)."""
    if not text:
        return []
    lang = detect_language(text)
    nlp_en, nlp_fr = get_nlp_models()
    nlp_model = nlp_fr if lang == "fr" else nlp_en

    clean_text = re.sub(r'<[^>]*>', ' ', text)
    clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_text)

    try:
        doc = nlp_model(clean_text)
    except Exception as e:
        logging.error(f"❌ Erreur NLP : {e}")
        return [w.lower() for w in re.findall(r'[a-zA-ZÀ-ÿ0-9]+', clean_text) if len(w) > 2]

    lemmas = []
    for token in doc:
        if not token.is_stop and not token.is_punct and not token.is_space and len(token.text) > 1:
            lemma = token.lemma_.lower().strip()
            if re.match(r'^[a-zÀ-ÿ0-9_\-\+\#\.]+$', lemma) and not lemma.isdigit():
                lemmas.append(lemma)
    return lemmas


def categorize_by_semantic_ontology(title, description, lemmas):
    """Détecte la catégorie d'un livre/ressource."""
    title_lower = title.lower() if title else ""
    desc_lower = description.lower() if description else ""

    scores = dict.fromkeys(CYBER_ONTOLOGY.keys(), 0)

    for cat, keywords in CYBER_ONTOLOGY.items():
        for kw in keywords:
            if " " in kw:
                if kw in title_lower:
                    scores[cat] += 4
                if kw in desc_lower:
                    scores[cat] += 2
            else:
                if kw in lemmas:
                    scores[cat] += 3
                if kw in title_lower:
                    scores[cat] += 2

    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        if any(k in title_lower or k in desc_lower for k in ["oscp", "ceh", "cissp", "cism", "comptia", "sans", "giac"]):
            return "Certifications"
        if any(k in title_lower or k in desc_lower for k in ["cheat sheet", "cheatsheet", "checklist", "reference", "aide-mémoire"]):
            return "Cheat Sheets / Références"
        return "Général / InfoSec"

    if best_cat == "offensive":
        return "Offensive / Red Team"
    elif best_cat == "defensive" or best_cat == "application_security":
        return "Defensive / Blue Team"
    elif best_cat == "governance":
        if any(k in title_lower for k in ["cert", "iso", "compliance"]):
            return "Certifications"
        return "Général / InfoSec"

    return "Général / InfoSec"


def detect_resource_type(title, description, url, category):
    """Détecte de manière experte le type de ressource à partir du titre, de la description, de l'URL et de la catégorie."""
    text = f"{title} {description if description else ''} {category if category else ''}".lower()
    url_lower = url.lower() if url else ""

    # 1. Threat-Intel
    threat_intel_markers = ["yara", "sigma", "threat-intel", "threat intel", "ioc-list", "ioc list", "iocs", "compromise", "signature de malware", "rules"]
    if any(m in text or m in url_lower for m in threat_intel_markers):
        if not any(x in text for x in ["course", "book", "livre", "guide"]):
            return "Threat-Intel"

    # 2. Hardening
    hardening_markers = ["hardening", "durcissement", "checklist", "cis-benchmark", "cis benchmark", "benchmarks", "security-checklist", "active-directory-hardening", "durcir", "securiser"]
    if any(m in text or m in url_lower for m in hardening_markers):
        return "Hardening"

    # 3. Write-up
    writeup_markers = ["writeup", "write-up", "ctf-writeup", "bugbounty", "bug bounty", "walkthrough", "poc-exploit", "poc", "exploit", "solution", "resolution"]
    if any(m in text or m in url_lower for m in writeup_markers):
        return "Write-up"

    # 4. Interview
    interview_markers = ["interview", "entretien", "embauche", "prep", "study-guide", "study guide", "exam", "certification", "oscp-notes", "cissp-study", "ceh-notes", "questions"]
    if any(m in text or m in url_lower for m in interview_markers):
        return "Interview"

    # 5. Template
    template_markers = ["template", "modele", "report", "rapport", "audit-template", "livrable", "pssi", "security-policy", "policy-sample"]
    if any(m in text or m in url_lower for m in template_markers):
        return "Template"

    # 6. Tool
    tool_markers = ["tool", "script", "program", "scanner", "utility", "exploit-db", "framework", "automatisation"]
    if any(m in text or m in url_lower for m in tool_markers) or "github.com/" in url_lower:
        # Si c'est un lien GitHub sans être un PDF ou autre, c'est probablement un outil
        if not any(ext in url_lower for ext in [".pdf", ".epub", ".mobi", "drive.google.com"]):
            return "Tool"

    # 7. Book (par défaut pour les PDF, cours, documents etc.)
    return "Book"
