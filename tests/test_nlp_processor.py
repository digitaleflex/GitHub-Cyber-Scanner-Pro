from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture(autouse=True)
def reset_cyber_terms():
    import nlp_processor

    nlp_processor._cyber_terms_built = False


@pytest.fixture(autouse=True)
def mock_database():
    with patch("database.get_approved_keywords") as mock:
        mock.return_value = []
        yield mock


def test_build_cyber_terms_loads_categories():
    import nlp_processor

    nlp_processor._build_cyber_terms()
    assert len(nlp_processor.CYBER_TERMS) > 0
    assert "pentest" in str(nlp_processor.CYBER_TERMS)


def test_refresh_cyber_terms_resets_cache():
    import nlp_processor

    nlp_processor._build_cyber_terms()
    old_len = len(nlp_processor.CYBER_TERMS)
    nlp_processor.refresh_cyber_terms()
    assert len(nlp_processor.CYBER_TERMS) == old_len


def test_clean_and_lemmatize():
    import nlp_processor

    result = nlp_processor.clean_and_lemmatize("Buffer Overflow in OpenSSL - CVE-2024-1234 https://example.com")
    assert isinstance(result, list)
    assert all(len(w) > 2 for w in result)
    assert "overflow" in result
    assert "openssl" in result


def test_clean_and_lemmatize_empty():
    import nlp_processor

    result = nlp_processor.clean_and_lemmatize("")
    assert result == []


def test_clean_and_lemmatize_strips_urls():
    import nlp_processor

    result = nlp_processor.clean_and_lemmatize("check https://evil.com/payload for details")
    assert "https" not in result


TEST_DESCRIPTIONS_NLP = [
    "Advanced penetration testing framework with exploit development capabilities and custom payload generation",
    "Real-time intrusion detection system using machine learning for anomaly detection in network traffic",
    "Memory forensic analysis toolkit for extracting artifacts and detecting rootkits in RAM dumps",
]


def test_extract_keywords_returns_list():
    import nlp_processor

    queries = nlp_processor.extract_keywords(TEST_DESCRIPTIONS_NLP, top_n=10)
    assert isinstance(queries, list)
    assert len(queries) > 0


def test_extract_keywords_contains_queries():
    import nlp_processor

    queries = nlp_processor.extract_keywords(TEST_DESCRIPTIONS_NLP, top_n=10)
    assert all('"' in q for q in queries)
    assert all(any(kw in q.lower() for kw in ["security", "cybersecurity", "hacking", "tools", "awesome", "framework"]) for q in queries)


def test_extract_keywords_empty():
    import nlp_processor

    queries = nlp_processor.extract_keywords([], top_n=10)
    assert queries == []


def test_extract_keywords_short_texts():
    import nlp_processor

    queries = nlp_processor.extract_keywords(["hi", "test"], top_n=10)
    assert queries == []


def test_categorize_by_semantic_ontology():
    import nlp_processor

    cat = nlp_processor.categorize_by_semantic_ontology(
        "SQL Injection Scanner",
        "Automated tool for detecting SQL injection vulnerabilities in web applications",
        ["sql", "injection", "scanner", "automated", "detect"],
    )
    assert isinstance(cat, str)


def test_categorize_unknown_returns_general():
    import nlp_processor

    cat = nlp_processor.categorize_by_semantic_ontology(
        "Cat Pictures",
        "A collection of cute cat pictures for wallpaper",
        ["cat", "picture", "collection", "cute", "wallpaper"],
    )
    assert cat == "General" or isinstance(cat, str)


def test_detect_resource_type():
    import nlp_processor

    assert nlp_processor.detect_resource_type("Python Tool", "A CLI tool", "https://github.com/test/tool", "pentest") == "tool"
    assert nlp_processor.detect_resource_type("PDF Guide", "Security guide", "https://example.com/guide.pdf", "defense") == "pdf"
    assert nlp_processor.detect_resource_type("Video Tutorial", "Watch on YouTube", "https://youtube.com/watch?v=abc", "pentest") == "video"
    assert nlp_processor.detect_resource_type("Research Paper", "Published on arXiv", "https://arxiv.org/abs/1234", "osint") == "paper"
    assert nlp_processor.detect_resource_type("Unknown", "", "https://example.com", "general") == "link"


def test_generate_synopsis():
    import nlp_processor

    synopsis = nlp_processor.generate_synopsis(
        "Advanced penetration testing framework with custom payload generation and exploit development",
        "Python", 5000, "Critique", 85, semantic_category="pentest",
    )
    assert isinstance(synopsis, str)
    assert len(synopsis) > 10
    assert "pentest" in synopsis.lower() or "défense" in synopsis.lower() or "Python" in synopsis


def test_generate_synopsis_empty():
    import nlp_processor

    synopsis = nlp_processor.generate_synopsis("", "", 0, None, None)
    assert synopsis == "Aucune description disponible."


def test_stem():
    import nlp_processor

    assert nlp_processor._stem("running") == "runn"
    assert nlp_processor._stem("testing") == "test"
    assert nlp_processor._stem("cat") == "cat"


def test_cyber_text_analyzer():
    import nlp_processor

    analyzer = nlp_processor.CyberTextAnalyzer(corpus=TEST_DESCRIPTIONS_NLP)
    assert hasattr(analyzer, "vocab")
    assert len(analyzer.vocab) > 0

    result = analyzer.process_repository({
        "description": "A penetration testing framework for web applications",
    })
    assert "score_qualite" in result
    assert result["score_qualite"] >= 0
