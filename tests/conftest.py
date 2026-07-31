import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture(autouse=True)
def mock_db_env():
    with patch.dict(os.environ, {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "test_scanner_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_pass",
    }):
        yield


@pytest.fixture
def mock_psycopg2():
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (0,)
        mock_cursor.fetchall.return_value = []
        mock_cursor.rowcount = 0
        mock_connect.return_value = mock_conn
        yield mock_connect, mock_conn, mock_cursor


@pytest.fixture
def mock_requests_get():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"objects": []}
        mock_response.text = ""
        mock_response.content = b""
        mock_get.return_value = mock_response
        yield mock_get, mock_response
