from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_db_conn():
    with patch("src.db.connection.get_db_connection") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_cursor


def _count_row(n):
    return {"c": n}


def test_unified_search_empty_query(mock_db_conn):
    from database import unified_search

    res = unified_search("")
    assert res["results"] == []
    assert res["total"] == 0
    assert res["pages"] == 0


def test_unified_search_short_query(mock_db_conn):
    from database import unified_search

    res = unified_search("a")
    assert res["results"] == []
    assert res["total"] == 0


def test_unified_search_returns_results(mock_db_conn):
    import database

    repo_row = {"name": "awesome-pentest-tool", "desc": "A pentest framework", "stars": 100,
                "lang": "Python", "url": "https://github.com/x/y", "security_verdict": "Critique",
                "vitality_score": 80, "result_type": "repo"}
    cve_row = {"name": "CVE-2024-1234", "desc": "Buffer overflow in TLS", "severity": "HIGH",
               "cvss_score": 9.1, "published": "2024-01-01", "result_type": "cve"}

    # 4 comptages (fetchone) puis selects + facettes (fetchall)
    mock_db_conn.fetchone.side_effect = [
        _count_row(1), _count_row(1), _count_row(0), _count_row(0),
    ]
    mock_db_conn.fetchall.side_effect = [
        [repo_row],  # select repo
        [cve_row],  # select cve
        [],  # select book
        [],  # select keyword
        [{"lang": "Python", "count": 1}],  # facet languages
        [{"severity": "HIGH", "count": 1}],  # facet severities
        [{"category": "threat", "count": 1}],  # facet categories
    ]

    res = database.unified_search("test", limit=30)
    assert isinstance(res, dict)
    assert res["total"] == 2
    assert len(res["results"]) == 2
    types = {r["result_type"] for r in res["results"]}
    assert "repo" in types
    assert "cve" in types
    assert res["facets"]["types"]["repo"] == 1
    assert res["facets"]["types"]["book"] == 0
    assert res["facets"]["languages"][0]["lang"] == "Python"
    assert res["facets"]["severities"]["HIGH"] == 1


def test_unified_search_handles_db_error():
    with patch("src.db.connection.get_db_connection", side_effect=Exception("DB DOWN")):
        from database import unified_search

        res = unified_search("test", limit=10)
        assert res["results"] == []
        assert res["total"] == 0


def test_unified_search_respects_limit(mock_db_conn):
    import database

    many_rows = [{"name": f"repo-{i}", "desc": "desc", "stars": 1, "lang": "py",
                  "url": "u", "security_verdict": None, "vitality_score": 1,
                  "result_type": "repo"} for i in range(100)]
    mock_db_conn.fetchone.side_effect = [
        _count_row(100), _count_row(0), _count_row(0), _count_row(0),
    ]
    mock_db_conn.fetchall.side_effect = [
        many_rows[:5],  # select repo (LIMIT 5 appliqué côté SQL)
        [],  # select cve
        [],  # select book
        [],  # select keyword
        [{"lang": "py", "count": 100}],  # facet languages
        [{"severity": "N/A", "count": 0}],  # facet severities
        [],  # facet categories
    ]

    res = database.unified_search("repo", limit=5)
    assert len(res["results"]) == 5
    assert res["per_page"] == 5
    assert res["total"] == 100


def test_unified_search_type_filter(mock_db_conn):
    import database

    cve_row = {"name": "CVE-2024-9999", "desc": "Critical remote code execution",
               "severity": "CRITICAL", "cvss_score": 9.8, "published": "2024-03-01",
               "result_type": "cve"}
    mock_db_conn.fetchone.side_effect = [
        _count_row(1), _count_row(1), _count_row(0), _count_row(0),
    ]
    mock_db_conn.fetchall.side_effect = [
        [cve_row],  # select cve
        [{"lang": None, "count": 1}],  # facet languages
        [{"severity": "CRITICAL", "count": 1}],  # facet severities
    ]

    res = database.unified_search("CVE-2024", types=["cve"])
    assert len(res["results"]) == 1
    assert res["results"][0]["result_type"] == "cve"
    assert res["facets"]["types"]["cve"] == 1


def test_unified_search_filters_and_sort(mock_db_conn):
    import database

    cve_row = {"name": "CVE-2024-8888", "desc": "Buffer overflow", "severity": "HIGH",
               "cvss_score": 9.1, "published": "2024-01-01", "result_type": "cve"}
    mock_db_conn.fetchone.side_effect = [
        _count_row(0), _count_row(1), _count_row(0), _count_row(0), _count_row(0),
    ]
    mock_db_conn.fetchall.side_effect = [
        [cve_row],  # select cve
        [{"severity": "HIGH", "count": 1}],  # facet severities
    ]

    res = database.unified_search("overflow", types=["cve"], severity="HIGH", sort="cvss")
    assert res["total"] == 1
    assert res["results"][0]["severity"] == "HIGH"
