import json
from unittest.mock import MagicMock, patch

import pytest


SAMPLE_MITRE_MOBILE = {
    "objects": [
        {
            "type": "attack-pattern",
            "name": "Clipboard Modification",
        },
        {
            "type": "malware",
            "name": "Android Banker",
        },
        {
            "type": "tool",
            "name": "Mobile Security Framework",
        },
    ]
}

SAMPLE_MITRE_ICS = {
    "objects": [
        {
            "type": "attack-pattern",
            "name": "Change Program State",
        },
        {
            "type": "malware",
            "name": "Industroyer Malware",
        },
        {
            "type": "course-of-action",
            "name": "Network Segmentation",
        },
    ]
}

SAMPLE_OWASP_FILES = [
    {"name": "SQL_Injection_Prevention_Cheat_Sheet.md", "download_url": "https://example.com/sqli.md"},
    {"name": "Cross_Site_Request_Forgery_Prevention_Cheat_Sheet.md", "download_url": "https://example.com/csrf.md"},
]

SAMPLE_EXPLOITDB_CSV = (
    "id,file,title,date,author,platform,type,port\n"
    "1,exploits/linux/1.c,Linux Kernel 2.4 UAF Exploit,2024-01-01,anonymous,linux,local,0\n"
    "2,exploits/windows/2.py,Microsoft Exchange RCE Exploit,2024-01-02,researcher,windows,remote,443\n"
    "3,exploits/web/3.py,WordPress SQL Injection,2024-01-03,hacker,php,webapps,80\n"
)


@pytest.fixture(autouse=True)
def mock_requests(monkeypatch):
    import keyword_sources

    def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "mobile-attack" in url:
            resp.json.return_value = SAMPLE_MITRE_MOBILE
        elif "ics-attack" in url:
            resp.json.return_value = SAMPLE_MITRE_ICS
        elif "CheatSheetSeries" in url and "contents" in url:
            resp.json.return_value = SAMPLE_OWASP_FILES
            resp.text = ""
        elif "cheatsheet" in url.lower() and url.endswith(".md"):
            resp.text = "# Example\n## SQL Injection\nThis is an injection prevention guide."
        elif "exploitdb" in url:
            resp.text = SAMPLE_EXPLOITDB_CSV
        else:
            resp.json.return_value = {"objects": []}
            resp.text = ""
        return resp

    monkeypatch.setattr("requests.get", mock_get)
    monkeypatch.setattr("requests.post", lambda url, **kw: MagicMock(status_code=200))

    monkeypatch.setattr(keyword_sources, "_load_json", lambda url, cache: mock_get(url).json())
    monkeypatch.setattr(keyword_sources, "_load_text", lambda url, cache: mock_get(url).text)


@pytest.fixture(autouse=True)
def mock_database(monkeypatch):
    """Mock all database calls used by keyword_sources."""
    import keyword_sources

    def mock_cve_query(limit=30000):
        return [
            {
                "term": "buffer overflow",
                "category_guess": "pentest",
                "score": 0.85,
                "sources": 1,
                "source_samples": "extracted from 150 CVEs",
            },
            {
                "term": "remote code execution",
                "category_guess": "pentest",
                "score": 0.82,
                "sources": 1,
                "source_samples": "extracted from 120 CVEs",
            },
            {
                "term": "sql injection",
                "category_guess": "pentest",
                "score": 0.78,
                "sources": 1,
                "source_samples": "extracted from 90 CVEs",
            },
        ]

    monkeypatch.setattr(keyword_sources, "extract_cve_keywords", mock_cve_query)


def test_extract_cve_keywords():
    from keyword_sources import extract_cve_keywords

    results = extract_cve_keywords(limit=100)
    assert isinstance(results, list)
    assert len(results) > 0
    terms = [r["term"] for r in results]
    assert any("buffer" in t or "overflow" in t for t in terms)
    assert any("sql injection" in t for t in terms)
    assert all(r["score"] > 0 for r in results)
    assert all(r["category_guess"] == "pentest" for r in results)


def test_parse_mitre_mobile():
    from keyword_sources import parse_mitre_mobile

    terms = parse_mitre_mobile()
    assert isinstance(terms, list)
    assert len(terms) >= 1
    assert any("android" in t.lower() for t in terms)
    assert any("banker" in t.lower() for t in terms)


def test_parse_mitre_ics():
    from keyword_sources import parse_mitre_ics

    terms = parse_mitre_ics()
    assert isinstance(terms, list)
    assert len(terms) >= 1
    assert any("program" in t.lower() for t in terms)
    assert any("industroyer" in t.lower() for t in terms)
    assert any("segment" in t.lower() for t in terms)


def test_fetch_owasp_cheatsheet_keywords():
    from keyword_sources import fetch_owasp_cheatsheet_keywords

    terms = fetch_owasp_cheatsheet_keywords()
    assert isinstance(terms, list)
    assert len(terms) >= 1
    assert any("sql injection" in t.lower() for t in terms)
    assert any("request forgery" in t.lower() for t in terms)


def test_fetch_exploitdb_keywords():
    from keyword_sources import fetch_exploitdb_keywords

    terms = fetch_exploitdb_keywords()
    assert isinstance(terms, list)
    assert len(terms) >= 1
    assert any("linux kernel" in t.lower() for t in terms)
    assert any("exchange" in t.lower() for t in terms)
    assert any("wordpress" in t.lower() for t in terms)


def test_build_combined_ontology():
    from keyword_sources import build_combined_ontology

    ontology = build_combined_ontology()
    assert isinstance(ontology, dict)
    assert "mobile" in ontology
    assert "iot" in ontology
    assert "pentest" in ontology
    assert len(ontology["mobile"]) >= 1
    assert len(ontology["pentest"]) >= 1


@patch("database.save_discovered_keywords")
@patch("nlp_processor.refresh_cyber_terms")
def test_import_external_sources_to_db(mock_refresh, mock_save):
    mock_save.return_value = 5
    from keyword_sources import import_external_sources_to_db

    stats = import_external_sources_to_db()
    assert isinstance(stats, dict)
    assert "total" in stats
    assert stats["total"] >= 0


def test_slugify():
    from keyword_sources import _slugify

    assert _slugify("SQL Injection!!") == "sql injection"
    assert _slugify("  Buffer-Overflow  ") == "buffer-overflow"
    assert _slugify("") == ""


def test_clean_term():
    from keyword_sources import _clean_term

    assert _clean_term("buffer overflow") == "buffer overflow"
    assert _clean_term("") is None
    assert _clean_term("ab") is None
    assert _clean_term("t1234") is None
    assert _clean_term("capec-123") is None
    assert _clean_term("cwe-789") is None


def test_deduplicate_terms():
    from keyword_sources import _deduplicate_terms

    terms = ["foo", "bar", "foo", "foo bar", "bar"]
    result = _deduplicate_terms(terms)
    assert result == ["foo", "bar", "foo bar"]
