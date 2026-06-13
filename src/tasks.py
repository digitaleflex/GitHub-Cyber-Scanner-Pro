import os
import logging
from celery import Celery
import database
import scanner
import nlp_processor
from security_analyzer import SecurityAnalyzer

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Configuration Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

app = Celery("cyber_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@app.task(name="task_osint_scan")
def task_osint_scan(repo_url, repo_name, repo_data=None):
    """Tâche pour scanner un dépôt GitHub (README -> Ressources)."""
    logging.info(f"📥 [Celery] Début du scan pour {repo_name} ({repo_url})")
    try:
        repo_id = repo_url.split("/")[-1]
        
        if repo_data:
            repo_item = {
                "id": repo_id,
                "full_name": repo_name,
                "html_url": repo_url,
                "stargazers_count": repo_data.get("stars", 0),
                "description": repo_data.get("description", ""),
                "language": repo_data.get("language", ""),
                "updated_at": repo_data.get("updated_at", "")
            }
        else:
            # Simuler un item GitHub minimal
            repo_item = {
                "id": repo_id,
                "full_name": repo_name,
                "html_url": repo_url,
                "stargazers_count": 0,
                "description": "",
                "updated_at": ""
            }
        
        # Enregistrer/Mettre à jour le dépôt (ceci déclenche aussi l'analyse NLP initiale)
        database.save_repositories([repo_item])
        
        # Parser le README pour extraire les ressources (livres, liens, etc.)
        scanner.fetch_and_parse_readme(repo_id, repo_name, repo_item["description"])
        
        return f"✅ Scan terminé pour {repo_name}"
    except Exception as e:
        logging.error(f"❌ Erreur lors de la tâche task_osint_scan pour {repo_name}: {e}")
        return str(e)

@app.task(name="task_nlp_analysis")
def task_nlp_analysis(repo_id):
    """Tâche d'analyse NLP approfondie et sauvegarde vectorielle."""
    logging.info(f"🧠 [Celery] Analyse NLP pour le dépôt {repo_id}")
    try:
        # Récupérer les infos du dépôt
        conn = database.get_db_connection()
        cursor = conn.cursor(cursor_factory=database.RealDictCursor)
        cursor.execute("SELECT * FROM repositories WHERE id = %s", (repo_id,))
        repo = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not repo:
            return f"⚠️ Dépôt {repo_id} non trouvé"
            
        # Analyser
        analyzer = nlp_processor.CyberTextAnalyzer()
        analysis = analyzer.process_repository(repo)
        
        # Sauvegarder dans PostgreSQL (pgvector)
        database.update_repo_quality_and_vector(repo_id, analysis["score_qualite"], analysis["vecteur_semantique"])
        
        # Sauvegarder dans Qdrant
        payload = {
            "full_name": repo["full_name"],
            "description": repo["description"],
            "score_qualite": analysis["score_qualite"]
        }
        database.save_to_qdrant(repo_id, analysis["vecteur_semantique"], payload)
        
        return f"✅ Analyse NLP terminée pour {repo_id}"
    except Exception as e:
        logging.error(f"❌ Erreur lors de la tâche task_nlp_analysis pour {repo_id}: {e}")
        return str(e)

@app.task(name="task_security_audit")
def task_security_audit(repo_url, repo_id):
    """Effectue un audit de sécurité complet et sauvegarde le résultat."""
    logging.info(f"🛡️ [Celery] Début de l'audit sécurité pour {repo_id}")
    try:
        # Récupérer l'URL complète si non fournie (sécurité)
        if not repo_url.startswith("http"):
            # Chercher en base
            conn = database.get_db_connection()
            cursor = conn.cursor(cursor_factory=database.RealDictCursor)
            cursor.execute("SELECT html_url FROM repositories WHERE id = %s", (repo_id,))
            repo = cursor.fetchone()
            cursor.close()
            conn.close()
            if repo:
                repo_url = repo["html_url"]
            else:
                return f"❌ Impossible de trouver l'URL pour le dépôt {repo_id}"

        analyzer = SecurityAnalyzer()
        report = analyzer.analyze_repository(repo_url)
        
        # Sauvegarder en base
        database.save_security_audit(repo_id, report["verdict"], report)
        
        return f"✅ Audit terminé pour {repo_id} : Verdict {report['verdict']}"
    except Exception as e:
        logging.error(f"❌ Erreur audit sécurité pour {repo_id}: {e}")
        return str(e)
