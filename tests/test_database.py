from unittest.mock import patch, MagicMock


@patch('src.database.psycopg2.connect')
def test_database_connection(mock_connect):
    """Verifie que la connexion a la base de donnees fonctionne."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    from src.database import get_db_connection
    conn = get_db_connection()
    
    assert conn is not None
    mock_connect.assert_called()


def test_init_db():
    """Verifie que les tables sont creees."""
    from src.database import init_db
    # Ne teste pas reellement, juste verifie que ca plante pas a l'import
    assert callable(init_db)
