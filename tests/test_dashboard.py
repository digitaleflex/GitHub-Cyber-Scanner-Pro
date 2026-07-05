from scripts.dashboard import generate_html


def test_generate_html_writes_dashboard(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    repos = [
        {
            "name": "example-repo",
            "url": "https://example.com/example-repo",
            "stars": 42,
            "lang": "Python",
            "desc": "A sample repository",
            "updated": "2024-01-02T00:00:00Z",
        }
    ]

    generate_html(repos)

    html_files = list((tmp_path / "reports").glob("dashboard_*.html"))
    assert len(html_files) == 1

    html = html_files[0].read_text()
    assert "CyberScan Dashboard" in html
    assert "example-repo" in html
