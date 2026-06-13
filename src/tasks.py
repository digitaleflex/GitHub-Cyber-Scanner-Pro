import os
import asyncio
from celery import Celery
from src.osint_harvester import OSINTHarvester
from src.realtime_watcher import RealTimeWatcher
from src.security_analyzer import SecurityAnalyzer
import database

# Configuration de Celery
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://cyber-queue:6379/0")
app = Celery("cyber_tasks", broker=REDIS_URL, backend=REDIS_URL)

# Configuration des files d'attente
app.conf.task_routes = {
    "src.tasks.mass_harvest": {"queue": "harvester"},
    "src.tasks.process_nlp": {"queue": "nlp"},
    "src.tasks.run_security_scan": {"queue": "security"},
}

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configuration des tâches planifiées (Cron jobs)."""
    # Lancer le RealTimeWatcher toutes les 5 minutes
    sender.add_periodic_task(300.0, monitor_github_events.s(), name="GHArchive Watcher")
    
    # Lancer un moissonnage de masse toutes les nuits à 2h du matin
    # sender.add_periodic_task(crontab(hour=2, minute=0), mass_harvest.s(), name="Nightly Harvester")

@app.task
def monitor_github_events():
    """Tâche périodique pour la découverte instantanée."""
    watcher = RealTimeWatcher()
    asyncio.run(watcher.monitor_loop())

@app.task
def run_security_scan(repo_url, repo_id):
    """Tâche d'audit de sécurité (Trivy/Semgrep)."""
    analyzer = SecurityAnalyzer()
    report = analyzer.analyze_repository(repo_url)
    
    # Enregistrer le verdict en base de données
    database.update_repo_security(repo_id, report["verdict"], report)
    return report["verdict"]

@app.task
def mass_harvest(dorks_map):
    """Tâche de moissonnage massif via Dorks."""
    harvester = OSINTHarvester()
    asyncio.run(harvester.run_dork_pipeline(dorks_map))
