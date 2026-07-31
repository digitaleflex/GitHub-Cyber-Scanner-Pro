from unittest.mock import MagicMock, patch

import pytest


SAMPLE_MITRE_ENTERPRISE = {
    "objects": [
        {
            "type": "attack-pattern",
            "name": "Spearphishing Attachment",
        },
        {
            "type": "malware",
            "name": "Emotet Malware",
        },
        {
            "type": "tool",
            "name": "Mimikatz Tool",
        },
        {
            "type": "intrusion-set",
            "name": "APT29 Group",
        },
        {
            "type": "course-of-action",
            "name": "User Account Control",
        },
        {
            "type": "campaign",
            "name": "Operation Wocao",
        },
        {
            "type": "attack-pattern",
            "name": "Process Injection",
        },
        {
            "type": "attack-pattern",
            "name": "T1134 Filler",
        },
    ]
}

SAMPLE_CAPEC_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Attack_Pattern_Catalog xmlns="http://capec.mitre.org/capec-3">
  <Attack_Pattern ID="1" Name="Buffer Overflow via Environment Variables"/>
  <Attack_Pattern ID="2" Name="SQL Injection"/>
  <Attack_Pattern ID="3" Name="Cross-Site Scripting (XSS)"/>
</Attack_Pattern_Catalog>
"""

SAMPLE_CWE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Weakness_Catalog xmlns="http://cwe.mitre.org/cwe-6">
  <Weakness ID="79" Name="Cross-site Scripting"/>
  <Weakness ID="89" Name="SQL Injection"/>
  <Weakness ID="119" Name="Buffer Overflow"/>
</Weakness_Catalog>
"""


@pytest.fixture(autouse=True)
def mock_requests(monkeypatch):
    import ontology_enricher

    def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "enterprise-attack" in url:
            resp.json.return_value = SAMPLE_MITRE_ENTERPRISE
        elif "capec" in url:
            resp.text = SAMPLE_CAPEC_XML
        elif "cwec" in url:
            import zipfile
            from io import BytesIO
            buf = BytesIO()
            with zipfile.ZipFile(buf, "w") as z:
                z.writestr("cwec_latest.xml", SAMPLE_CWE_XML)
            resp.content = buf.getvalue()
        else:
            resp.json.return_value = {"objects": []}
        return resp

    monkeypatch.setattr("requests.get", mock_get)
    monkeypatch.setattr(ontology_enricher, "_load_json", lambda url, cache: mock_get(url).json())
    monkeypatch.setattr(ontology_enricher, "_load_text", lambda url, cache: mock_get(url).text)
    monkeypatch.setattr(ontology_enricher, "_load_zip_text", lambda url, cache: mock_get(url).content)


@pytest.fixture(autouse=True)
def mock_db_for_import(monkeypatch):
    def mock_save(kwargs):
        return len(kwargs)

    def mock_approve(term, status, category):
        return True

    monkeypatch.setattr("database.save_discovered_keywords", mock_save)
    monkeypatch.setattr("database.approve_keyword", mock_approve)

    with patch("nlp_processor.refresh_cyber_terms") as mock:
        yield mock


def test_parse_mitre_attack():
    from ontology_enricher import parse_mitre_attack

    result = parse_mitre_attack(SAMPLE_MITRE_ENTERPRISE)
    assert isinstance(result, dict)
    assert "pentest" in result
    assert "malware" in result
    assert "red-team" in result
    assert "defense" in result
    assert any("spearphishing" in t.lower() for t in result["pentest"])
    assert any("process injection" in t.lower() for t in result["pentest"])
    assert any("emotet" in t.lower() for t in result["malware"])
    assert any("mimikatz" in t.lower() for t in result["red-team"])
    assert any("account" in t.lower() or "control" in t.lower() for t in result["defense"])
    assert any("apt29" in t.lower() or "woaco" in t.lower() for t in result["red-team"])


def test_parse_capec():
    from ontology_enricher import parse_capec

    terms = parse_capec(SAMPLE_CAPEC_XML)
    assert isinstance(terms, list)
    assert len(terms) >= 2
    assert any("buffer overflow" in t.lower() for t in terms)
    assert any("sql injection" in t.lower() for t in terms)


def test_parse_cwe():
    from ontology_enricher import parse_cwe

    terms = parse_cwe(SAMPLE_CWE_XML)
    assert isinstance(terms, list)
    assert len(terms) >= 2
    assert any("cross-site" in t.lower() for t in terms)
    assert any("buffer overflow" in t.lower() for t in terms)


def test_build_ontology():
    from ontology_enricher import build_ontology

    ontology = build_ontology()
    assert isinstance(ontology, dict)
    assert len(ontology) >= 5
    assert any(len(v) > 0 for v in ontology.values())
    assert "pentest" in ontology
    assert "malware" in ontology


def test_import_ontology_to_db():
    from ontology_enricher import import_ontology_to_db

    count = import_ontology_to_db()
    assert count >= 0
    assert isinstance(count, int)


def test_enrich_categories():
    from ontology_enricher import enrich_categories

    ontology = enrich_categories()
    assert isinstance(ontology, dict)
    assert "pentest" in ontology


def test_slugify():
    from ontology_enricher import _slugify

    assert _slugify("Process Injection!!") == "process injection"
    assert _slugify("  SQL-Injection  ") == "sql-injection"
    assert _slugify("") == ""


def test_clean_term():
    from ontology_enricher import _clean_term

    assert _clean_term("buffer overflow") == "buffer overflow"
    assert _clean_term("") is None
    assert _clean_term("ab") is None
    assert _clean_term("t1134") is None
    assert _clean_term("capec-123") is None
    assert _clean_term("cwe-79") is None


def test_extract_terms():
    from ontology_enricher import _extract_terms

    terms = _extract_terms("Buffer Overflow on Windows", max_n=3)
    assert "buffer" in terms
    assert "buffer overflow" in terms
    assert "buffer overflow on" in terms

    terms_skip = _extract_terms("Buffer Overflow on Windows", max_n=3, skip_unigrams=True)
    assert "buffer" not in terms_skip
    assert "buffer overflow" in terms_skip
