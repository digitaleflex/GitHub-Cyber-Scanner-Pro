from src.nlp_processor import NLPProcessor


def test_nlp_processor_initialization():
    """Vérifie que le processeur NLP s'initialise correctement et charge le modèle Spacy."""
    processor = NLPProcessor(language="fr")
    assert processor.nlp is not None

def test_lemmatization():
    """Vérifie que la lemmatisation fonctionne correctement."""
    processor = NLPProcessor(language="fr")
    text = "Les attaques informatiques sécurisées"
    result = processor.clean_and_lemmatize(text)
    # Vérifie que "attaques" est lemmatisé en "attaque", "sécurisées" en "sécurisé"
    assert "attaque" in result
    assert "sécuriser" in result or "sécurisé" in result

def test_ontology_classification():
    """Vérifie la classification avec l'ontologie."""
    processor = NLPProcessor(language="fr")
    text = "outil de fuzzing pour trouver des vulnérabilités"
    lemmas = processor.clean_and_lemmatize(text)
    categories = processor.classify_with_ontology(lemmas)
    assert "Offensive Security" in categories or "Vulnerability Assessment" in categories

def test_extract_key_phrases():
    """Vérifie l'extraction des phrases clés."""
    processor = NLPProcessor(language="fr")
    text = "Scanner de vulnérabilités réseau"
    keywords = processor.extract_key_phrases(text)
    assert len(keywords) > 0
    assert any("vulnérabilité" in kw or "réseau" in kw for kw in keywords)
