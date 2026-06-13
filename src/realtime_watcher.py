import asyncio
import datetime
import gzip
import io
import json
import logging

from osint_harvester import OSINTHarvester
from utils.http_client import StealthClient

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class RealTimeWatcher:
    """
    Algorithme de surveillance temps réel basé sur GitHub Archive (GHArchive).
    Détecte les nouveaux dépôts cyber à la seconde mondiale.
    """

    def __init__(self):
        self.harvester = OSINTHarvester()
        self.processed_events = set()
        self.cyber_keywords = ["cybersecurity", "hacking", "pentest", "exploit", "redteam", "blueteam", "malware"]

    async def fetch_latest_events(self, client):
        """
        Télécharge le dernier bloc d'événements (par fenêtre de 1h, archivé par GHArchive).
        """
        # Format GHArchive : https://data.gharchive.org/YYYY-MM-DD-H.json.gz
        now = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        url = f"https://data.gharchive.org/{now.strftime('%Y-%m-%d-%H')}.json.gz"

        logging.info(f"📡 Surveillance du flux temps réel : {url}")

        response = await client.get(url, timeout=30)
        if not response or response.status_code != 200:
            logging.warning("⚠️ Flux GHArchive temporairement indisponible ou trop récent.")
            return []

        # Décompression du flux JSONL (JSON Lines)
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
            events = [json.loads(line) for line in f]

        return events

    def is_cyber_related(self, event):
        """
        Filtre sémantique rapide sur l'événement pour détecter la pertinence cyber.
        """
        # On surveille principalement les créations de dépôts (CreateEvent) ou les nouveaux pushs
        if event.get("type") not in ["CreateEvent", "WatchEvent"]:
            return False

        repo_name = event.get("repo", {}).get("name", "").lower()
        # On vérifie si un mot-clé cyber est dans le nom du repo
        return any(kw in repo_name for kw in self.cyber_keywords)

    async def monitor_loop(self):
        """
        Boucle infinie de surveillance (check toutes les 5 minutes).
        """
        async with StealthClient() as client:
            while True:
                try:
                    events = await self.fetch_latest_events(client)
                    new_discoveries = 0

                    for event in events:
                        event_id = event.get("id")
                        if event_id in self.processed_events:
                            continue

                        if self.is_cyber_related(event):
                            repo_name = event["repo"]["name"]
                            repo_url = f"https://github.com/{repo_name}"

                            logging.info(f"✨ Nouveau dépôt cyber détecté en direct : {repo_name}")

                            # On lance l'analyse complète via le Harvester
                            await self.harvester.process_url(
                                client, 
                                repo_url, 
                                f"GitHub Discovery: {repo_name}",
                                repo_id=f"GH_LIVE_{event_id}"
                            )
                            new_discoveries += 1

                        self.processed_events.add(event_id)

                    # Nettoyage du cache des événements pour ne pas saturer la RAM
                    if len(self.processed_events) > 50000:
                        self.processed_events.clear()

                    logging.info(f"💤 Fin de cycle. Découvertes : {new_discoveries}. Pause avant prochain scan.")
                    await asyncio.sleep(300) # Attendre 5 minutes (Rythme GHArchive)

                except Exception as e:
                    logging.error(f"🔥 Erreur dans la boucle RealTimeWatcher : {e}")
                    await asyncio.sleep(60)

if __name__ == "__main__":
    watcher = RealTimeWatcher()
    # asyncio.run(watcher.monitor_loop())
    print("🚀 Algorithme RealTimeWatcher opérationnel (GitHub Archive).")
