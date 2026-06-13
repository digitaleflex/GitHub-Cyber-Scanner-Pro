from src.nlp_processor import clean_and_lemmatize


def test_lemmatization():
    """Vérifie que la lemmatisation nettoie correctement le texte."""
    text = "This is a simple hacking tutorial."
    lemmas = clean_and_lemmatize(text)
    assert "hack" in lemmas or "hacking" in lemmas
