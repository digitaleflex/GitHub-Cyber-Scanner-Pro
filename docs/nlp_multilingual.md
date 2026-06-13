# 🌐 Architecture Sémantique Multilingue & Bilinguisme (EN/FR) 🧠

Ce document spécifie la configuration et l'implémentation de l'analyseur sémantique multilingue bilingue (Français/Anglais) pour le **GitHub Cyber Scanner Pro**.

---

## 1. Principe de l'Alignement Vectoriel

Pour éviter le biais linguistique lié aux modèles d'IA purement anglophones, nous utilisons un espace vectoriel universel (cross-lingual embeddings) :
* **Modèle recommandé :** `paraphrase-multilingual-MiniLM-L12-v2` (ou `intfloat/multilingual-e5-small`).
* **Fonctionnement :** Les textes en français et en anglais décrivant les mêmes concepts cyber partagent des coordonnées vectorielles extrêmement proches (proximité cosinusoïdale).

---

## 💻 Spécification du Code (src/nlp_multilingual.py)

Voici le code de référence de l'analyseur multilingue à intégrer dans le projet :

```python
import os
import spacy
from sentence_transformers import SentenceTransformer

# 1. Chargement des pipelines de langues pour SpaCy
# À installer dans le Dockerfile : 
# RUN python -m spacy download en_core_web_sm && python -m spacy download fr_core_news_sm
try:
    nlp_en = spacy.load("en_core_web_sm")
    nlp_fr = spacy.load("fr_core_news_sm")
except OSError:
    raise ImportError("Veuillez installer les modèles SpaCy FR (fr_core_news_sm) et EN (en_core_web_sm).")

# 2. Chargement du modèle IA sémantique MULTILINGUE
# Ce modèle gère nativement le Français et l'Anglais dans le même espace vectoriel
encoder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

class MultilingualCyberAnalyzer:
    
    def detect_language(self, text):
        """Détecteur de langue ultra-rapide basé sur des mots-clés pivots cyber.
        Évite d'installer une bibliothèque lourde supplémentaire.
        """
        text_lower = text.lower()
        fr_indicators = ["sécurité", "système", "logiciel", "outil", "livre", "cours", "guide", "réseau"]
        
        fr_score = sum(1 for word in fr_indicators if word in text_lower)
        # Par défaut, si peu d'indices FR, on traite en Anglais (jargon mondial)
        return "fr" if fr_score > 1 else "en"

    def extract_keywords_by_language(self, text, lang):
        """Extrait les lemmes et groupes nominaux en utilisant le bon dictionnaire de langue."""
        doc = nlp_fr(text.lower()) if lang == "fr" else nlp_en(text.lower())
        keywords = []
        
        for chunk in doc.noun_chunks:
            clean_chunk = " ".join([token.lemma_ for token in chunk if not token.is_stop])
            if len(clean_chunk.split()) >= 1 and len(clean_chunk) > 2:
                keywords.append(clean_chunk)
        return list(set(keywords))

    def process_repository(self, repo_data):
        desc = repo_data.get("description", "")
        if not desc:
            return None

        # 1. Détection de la langue de la ressource
        lang = self.detect_language(desc)

        # 2. Extraction des mots-clés avec le modèle de grammaire adapté (FR ou EN)
        keywords = self.extract_keywords_by_language(desc, lang)

        # 3. Génération du vecteur SÉMANTIQUE UNIVERSEL (Multilingue)
        # Que le texte soit en FR ou en EN, le vecteur généré sera comparable !
        vector = encoder.encode(desc).tolist()

        return {
            "langue_detectee": lang,
            "mots_cles": keywords,
            "vecteur_semantique": vector
        }
```

---

## 🔍 Logique des Requêtes Utilisateurs (Bilingue)

1. **Vectorisation de la requête :** L'utilisateur soumet sa recherche (ex: *"Guide pour sécuriser Linux"*). Le script Python transforme cette phrase en vecteur avec `paraphrase-multilingual-MiniLM-L12-v2`.
2. **Recherche Vectorielle (Qdrant) :** Le vecteur de la requête est recherché dans la collection vectorielle via Qdrant.
3. **Résultat aligné :** Le moteur remonte indifféremment et de manière pertinente :
   * Les ressources en français (ex: *"Guide de durcissement du noyau Linux"*).
   * Les ressources en anglais (ex: *"An automated script for Linux kernel hardening"*).
