from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_semantic_classifier():
    with patch("keyword_miner.classify_semantic") as mock:
        mock.return_value = ("pentest", 0.85)
        yield mock


SAMPLE_DESCRIPTIONS = [
    "Advanced malware detection engine using behavioral analysis and machine learning",
    "Penetration testing toolkit with exploit development and payload generation features",
    "Cloud security auditing tool for AWS IAM policy review and configuration assessment",
    "Real-time intrusion detection system using deep packet inspection techniques",
    "Cryptographic library implementing AES-256-GCM with hardware acceleration support",
    "Memory forensic analysis toolkit for extracting artifacts from RAM dumps",
    "Mobile application security testing framework for reverse engineering Android apps",
    "Threat hunting platform with sigma rule integration and automated detection",
    "Ransomware analysis toolkit for decrypting files and recovering encrypted data",
    "Phishing detection framework using email header analysis and link scanning",
    "Zero day exploit research focusing on browser vulnerabilities and sandbox escape",
    "Endpoint detection and response agent with real-time monitoring and alerting capability",
    "Firewall rule analyzer for auditing network security policies and access control lists",
    "Vulnerability scanner for web applications with automatic crawling and form fuzzing",
    "Incident response playbook automation tool for SOAR platforms and ticketing systems",
    "Password cracking workstation using GPU acceleration and distributed hash computation",
    "DNS tunneling detection through deep packet inspection and traffic anomaly analysis",
    "Behavioral biometrics authentication system using keystroke dynamics and mouse tracking",
    "Container security scanner for Docker images and Kubernetes pod configuration validation",
    "Wireless network auditor supporting WPA3 handshake capture and deauthentication attacks",
    "Binary diffing tool for patch analysis and vulnerability research on firmware updates",
    "Cuckoo sandbox integration for automated malware analysis and behavior reporting",
    "SIEM rule generator for correlation across firewall logs and endpoint telemetry data",
    "Active directory security assessment tool for privilege escalation path discovery",
    "Rust based port scanner with SYN flood detection and service fingerprinting",
]


def test_mine_keywords_returns_list():
    from keyword_miner import mine_keywords

    results = mine_keywords(SAMPLE_DESCRIPTIONS, top_n=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_mine_keywords_contains_expected_terms():
    from keyword_miner import mine_keywords

    results = mine_keywords(SAMPLE_DESCRIPTIONS, top_n=50)
    assert len(results) > 0
    for r in results:
        assert len(r["term"]) >= 3
        assert r["score"] > 0
        assert "category_guess" in r
        assert "source_samples" in r


def test_mine_keywords_scores_positive():
    from keyword_miner import mine_keywords

    results = mine_keywords(SAMPLE_DESCRIPTIONS, top_n=50)
    for r in results:
        assert r["score"] > 0
        assert r["sources"] >= 1


def test_mine_keywords_respects_top_n():
    from keyword_miner import mine_keywords

    results = mine_keywords(SAMPLE_DESCRIPTIONS, top_n=5)
    assert len(results) <= 5


def test_mine_keywords_empty_input():
    from keyword_miner import mine_keywords

    results = mine_keywords([], top_n=50)
    assert results == []


def test_mine_keywords_with_news():
    from keyword_miner import mine_keywords

    news = [
        "New zero-day exploit discovered in Apache Log4j affecting millions of servers worldwide",
        "Critical vulnerability in Kubernetes allows privilege escalation in container environments",
    ]
    results = mine_keywords(SAMPLE_DESCRIPTIONS, news_texts=news, top_n=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_mine_keywords_short_descriptions():
    from keyword_miner import mine_keywords

    short_descs = ["hi", "test", "a", ""]
    results = mine_keywords(short_descs, top_n=50)
    assert results == []


def test_enrich_static_keywords():
    with patch("database.get_approved_keywords") as mock:
        mock.return_value = [
            {"term": "buffer overflow", "category_guess": "pentest", "score": 0.95},
            {"term": "ransomware analysis", "category_guess": "malware", "score": 0.90},
        ]
        from keyword_miner import enrich_static_keywords

        terms = enrich_static_keywords()
        assert "buffer overflow" in terms
        assert "ransomware analysis" in terms
        assert len(terms) == 2


def test_score_term():
    from collections import Counter
    from keyword_miner import _score_term

    doc_freq = Counter({"buffer overflow": 10, "sql injection": 5})
    term_freq = Counter({"buffer overflow": 15, "sql injection": 8})
    cyber_doc_freq = Counter({"buffer overflow": 8, "sql injection": 4})

    score = _score_term("buffer overflow", doc_freq, term_freq, 100, cyber_doc_freq, 40)
    assert score > 0

    score_low = _score_term("rare term", Counter({"rare term": 1}), Counter({"rare term": 1}), 100, Counter(), 40)
    assert score_low == 0.0


def test_is_valid_term():
    from keyword_miner import _is_valid_term

    assert _is_valid_term("buffer overflow")
    assert _is_valid_term("memory forensics")
    assert _is_valid_term("ransomware analysis")
    assert _is_valid_term("threat hunting")
    assert not _is_valid_term("a")
    assert not _is_valid_term("")
    assert not _is_valid_term("the and for")
    assert not _is_valid_term("https")


def test_tokenize():
    from keyword_miner import _tokenize

    tokens = _tokenize("Buffer Overflow in OpenSSL - CVE-2024-1234")
    assert "buffer" in tokens
    assert "overflow" in tokens
    assert "openssl" in tokens
    assert "http" not in tokens


def test_extract_ngrams():
    from keyword_miner import _extract_ngrams

    tokens = ["a", "buffer", "overflow", "test"]
    ngrams = _extract_ngrams(tokens)
    assert "buffer" in ngrams
    assert "buffer overflow" in ngrams
    assert "buffer overflow test" in ngrams
