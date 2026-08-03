"""Scan orchestration engine."""
import logging
import threading
import time
from src import database
from src.config import QUERIES, SCAN_INTERVAL_SECONDS
from src.collectors import fetch_github_data, parse_unprocessed_readmes
import src.nlp_processor as nlp_processor


scanner_status = "Prêt / En sommeil"
scanner_lock = threading.Lock()
scan_in_progress = False

bulk_lock = threading.Lock()
bulk_in_progress = False

harvest_in_progress = False

cve_in_progress = False


def scan_cycle():
    """Effectue un cycle de scan GitHub hybride (popularité et activité récente)."""
    logging.info("🔄 Début du cycle de scan sur GitHub...")
    new_discoveries_total = 0
    any_success = False

    # Phase 1: scan avec les queries statiques
    for query in QUERIES:
        # 1. Recherche par popularité (stars)
        logging.info(f"🔍 Recherche (Popularité) pour : {query}...")
        raw_items_stars, rate_limit_hit = fetch_github_data(query, sort_by="stars")

        if rate_limit_hit:
            logging.warning("⚠️ Cycle de scan interrompu en raison d'une limite de quota API non résolue.")
            break

        if raw_items_stars:
            any_success = True
            new_discoveries = database.save_repositories(raw_items_stars)
            new_discoveries_total += new_discoveries

        time.sleep(2.5)

        # 2. Recherche par activité récente (updated) pour découvrir les nouveaux dépôts / pépites
        logging.info(f"🔍 Recherche (Nouveautés récentes) pour : {query}...")
        raw_items_updated, rate_limit_hit = fetch_github_data(query, sort_by="updated")

        if rate_limit_hit:
            logging.warning("⚠️ Cycle de scan interrompu en raison d'une limite de quota API non résolue.")
            break

        if raw_items_updated:
            any_success = True
            new_discoveries = database.save_repositories(raw_items_updated)
            new_discoveries_total += new_discoveries

        time.sleep(2.5)

    # Phase 2: générer des queries dynamiques via NLP et scanner les nouveaux mots-clés
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM repositories WHERE description IS NOT NULL AND description != ''")
        descriptions = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        if descriptions:
            dynamic_queries = nlp_processor.extract_keywords(descriptions, top_n=30)
            if dynamic_queries:
                logging.info(f"🧠 Phase NLP: {len(dynamic_queries)} nouvelles queries dynamiques")
                for query in dynamic_queries:
                    logging.info(f"🔍 (NLP) Recherche (Popularité) pour : {query}...")
                    raw_items, rate_hit = fetch_github_data(query, sort_by="stars")
                    if rate_hit:
                        break
                    if raw_items:
                        any_success = True
                        new = database.save_repositories(raw_items)
                        new_discoveries_total += new
                    time.sleep(2.5)

                    logging.info(f"🔍 (NLP) Recherche (Nouveautés) pour : {query}...")
                    raw_items, rate_hit = fetch_github_data(query, sort_by="updated")
                    if rate_hit:
                        break
                    if raw_items:
                        any_success = True
                        new = database.save_repositories(raw_items)
                        new_discoveries_total += new
                    time.sleep(2.5)
    except Exception as e:
        logging.error(f"❌ Erreur lors de la phase NLP dynamique: {e}")

    if any_success:
        if new_discoveries_total > 0:
            logging.info(f"✨ {new_discoveries_total} nouvelle(s) pépite(s) découverte(s) lors de ce cycle !")
        else:
            logging.info("ℹ️ Données existantes synchronisées. Aucun nouveau dépôt.")

        parse_unprocessed_readmes()
        try:
            vitality_updated = database.recalculate_vitality_scores()
            if vitality_updated:
                logging.info(f"📊 Scores de vitalite recalculés pour {vitality_updated} depot(s)")
        except Exception as e:
            logging.error(f"❌ Erreur lors du recalcul des scores de vitalite: {e}")
        try:
            sem_backfilled = database.backfill_semantic_categories(batch_size=500)
            if sem_backfilled:
                logging.info(f"🧠 Catégories sémantiques backfillées pour {sem_backfilled} dépôt(s)")
        except Exception as e:
            logging.error(f"❌ Erreur lors du backfill des catégories sémantiques: {e}")
        try:
            import src.harvest_artifacts as harvest_artifacts
            hres = harvest_artifacts.harvest_batch(limit=80)
            if hres["issues"] or hres["commits"]:
                logging.info(f"🌾 Harvest: {hres['issues']} issues, {hres['commits']} commits")
        except Exception as e:
            logging.error(f"❌ Erreur lors de la récolte d'artifacts: {e}")
        try:
            import src.embeddings as embeddings
            emb_count = embeddings.embed_unembedded_repos(limit=100)
            if emb_count:
                logging.info(f"🧬 Embeddings generes pour {emb_count} depot(s)")
        except Exception as e:
            logging.error(f"❌ Erreur embeddings: {e}")
        try:
            import src.agents.cve_agent as cve_agent
            n = cve_agent.batch_analyze_recent(limit=8)
            if n:
                logging.info(f"🤖 CVE Agent: {n} CVE analysees par IA")
        except Exception as e:
            logging.error(f"❌ Erreur CVE Agent: {e}")


def run_scan_once_manual():
    """Déclenche manuellement un scan unique."""
    global scan_in_progress, scanner_status
    with scanner_lock:
        if scan_in_progress:
            return
        scan_in_progress = True

    try:
        scanner_status = "Scan manuel en cours..."
        logging.info("⚡ Lancement d'un scan manuel...")
        scan_cycle()
        logging.info("⚡ Scan manuel terminé avec succès.")
    except Exception as e:
        logging.error(f"❌ Erreur lors du scan manuel : {e}")
    finally:
        scanner_status = "Prêt / En sommeil"
        scan_in_progress = False


def run_scanner_daemon():
    """Démon de scan périodique."""
    global scanner_status, scan_in_progress
    logging.info("🚀 Démarrage du démon de scan automatique...")

    # Attendre que Postgres soit prêt et migré
    time.sleep(15)

    while True:
        with scanner_lock:
            if not scan_in_progress:
                scan_in_progress = True
            else:
                time.sleep(60)
                continue

        try:
            scanner_status = "Scan automatique en cours..."
            scan_cycle()
        except Exception as e:
            logging.error(f"❌ Erreur lors du cycle de scan automatique : {e}")
        finally:
            scanner_status = "Prêt / En sommeil"
            scan_in_progress = False

        logging.info(f"💤 En sommeil pour {SCAN_INTERVAL_SECONDS // 60} minutes...")
        time.sleep(SCAN_INTERVAL_SECONDS)
