import logging
from psycopg2.extras import execute_values

import src.db.connection as _conn

BATCH_SIZE = 2000


def save_affected_products(products):
    """Upsert batch via execute_values (x100 vs INSERT individuel).

    Chaque item: cve_id, product, vendor, version, platform, cpe_uri, status.
    """
    if not products:
        return 0
    seen = set()
    rows = []
    for p in products:
        cve_id = (p.get("cve_id") or "").strip()
        cpe = (p.get("cpe_uri") or "").strip()
        if not cve_id:
            continue
        key = (cve_id, cpe, p.get("status", "unknown"))
        if key in seen:
            continue
        seen.add(key)
        rows.append((
            cve_id,
            (p.get("product") or "unknown")[:300],
            (p.get("vendor") or "")[:200] or None,
            (p.get("version") or "")[:200] or None,
            (p.get("platform") or "")[:100] or None,
            p.get("cpe_uri") or None,
            p.get("status", "unknown"),
        ))

    if not rows:
        return 0

    conn = _conn.get_db_connection()
    cursor = conn.cursor()
    inserted = 0
    try:
        execute_values(
            cursor,
            """
            INSERT INTO cve_affected_products
                (cve_id, product, vendor, version, platform, cpe_uri, status)
            VALUES %s
            ON CONFLICT (cve_id, COALESCE(cpe_uri, ''), COALESCE(vendor, ''), COALESCE(product, ''))
            DO NOTHING
            """,
            rows,
            page_size=BATCH_SIZE,
        )
        inserted = cursor.rowcount
    except Exception as ex:
        logging.error(f"Erreur batch save produits: {ex}")
    conn.commit()
    cursor.close()
    conn.close()
    return inserted


def get_products_count():
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cve_affected_products")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row else 0
    except Exception as e:
        logging.error(f"Erreur count produits: {e}")
        return -1


def get_products_for_cve(cve_id: str):
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT product, vendor, version, platform, cpe_uri, status
            FROM cve_affected_products
            WHERE cve_id = %s
            ORDER BY vendor NULLS LAST, product
            """,
            (cve_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                "product": r[0],
                "vendor": r[1],
                "version": r[2],
                "platform": r[3],
                "cpe_uri": r[4],
                "status": r[5],
            }
            for r in rows
        ]
    except Exception as e:
        logging.error(f"Erreur get products {cve_id}: {e}")
        return []
