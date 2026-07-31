import logging
import os
import time

import psycopg2

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "scanner_db")
DB_USER = os.getenv("DB_USER", "cyberscan")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cyberscan")


def get_db_connection():
    retries = 10
    delay = 3
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=5,
            )
            return conn
        except psycopg2.OperationalError as e:
            logging.warning(
                f"PostgreSQL non disponible. Tentative {attempt + 1}/{retries}... Erreur: {e}"
            )
            time.sleep(delay)
    logging.critical("Impossible de se connecter a PostgreSQL.")
    raise ConnectionError("Echec de connexion a PostgreSQL.")
