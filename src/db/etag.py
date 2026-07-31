import logging
import src.db.connection as _conn



def save_etag_to_cache(query, etag, last_modified):
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO etag_cache (query, etag, last_modified, last_checked)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (query) DO UPDATE 
            SET etag = EXCLUDED.etag, 
                last_modified = EXCLUDED.last_modified, 
                last_checked = CURRENT_TIMESTAMP
            """,
            (query, etag, last_modified)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur ETag cache: {e}")

def get_etag_from_cache(query):
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT etag, last_modified FROM etag_cache WHERE query = %s", (query,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return row[0], row[1]
    except Exception as e:
        logging.error(f"Erreur ETag read cache: {e}")
    return None, None
