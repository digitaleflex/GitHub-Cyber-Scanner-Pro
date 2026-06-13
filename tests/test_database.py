from unittest.mock import patch

from src.database import get_db_connection


@patch('src.database.psycopg2.connect')
def test_database_connection(mock_connect):
    """Vérifie que la connexion à la base de données est correctement initialisée."""
    conn = get_db_connection()
    assert conn is not None
    mock_connect.assert_called_once()
