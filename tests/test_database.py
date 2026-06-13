import pytest
from unittest.mock import MagicMock, patch
from src.database import PostgresDB

@patch('src.database.psycopg2.connect')
def test_database_connection(mock_connect):
    """Vérifie que la connexion à la base de données est correctement initialisée."""
    db = PostgresDB()
    # On simule un appel de connexion
    conn = db.get_connection()
    assert conn is not None
    mock_connect.assert_called_once()

@patch('src.database.psycopg2.connect')
def test_database_schema_creation(mock_connect):
    """Vérifie que la création du schéma s'exécute sans erreur."""
    db = PostgresDB()
    # Mocking du curseur
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    
    db.init_schema()
    
    # Vérifie que des requêtes de création ont été exécutées
    assert mock_cursor.execute.call_count > 0
    mock_connect.return_value.commit.assert_called_once()
    
def test_tsvector_query_formatting():
    """Vérifie que les requêtes TSVector sont bien formatées par la fonction (en mock)."""
    db = PostgresDB()
    query = "sql injection"
    formatted_query = db.format_tsquery(query)
    # Doit séparer par '&' ou '|' selon la logique
    assert "sql" in formatted_query
    assert "injection" in formatted_query
