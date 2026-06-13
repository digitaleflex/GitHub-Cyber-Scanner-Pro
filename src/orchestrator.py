import os
import importlib
import logging
import time
import database
from connectors.base_connector import BaseConnector

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class CyberOrchestrator:
    def __init__(self):
        self.connectors = []
        self.load_connectors()

    def load_connectors(self):
        """Charge dynamiquement tous les connecteurs du dossier src/connectors/."""
        connectors_dir = os.path.join(os.path.dirname(__file__), "connectors")
        logging.info(f"🔍 Recherche de connecteurs dans {connectors_dir}...")
        
        for filename in os.listdir(connectors_dir):
            if filename.endswith("_connector.py") and filename != "base_connector.py":
                module_name = f"connectors.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    # Trouver la classe dans le module qui hérite de BaseConnector
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, BaseConnector) and attr != BaseConnector:
                            self.connectors.append(attr())
                            logging.info(f"✅ Connecteur chargé : {attr_name} ({filename})")
                except Exception as e:
                    logging.error(f"❌ Impossible de charger le module {module_name} : {e}")

    def run_sync_cycle(self):
        """Lance une synchronisation complète de toutes les sources."""
        logging.info(f"🚀 Lancement du cycle de synchronisation ({len(self.connectors)} sources)...")
        
        for connector in self.connectors:
            try:
                logging.info(f"📡 Synchro en cours : {connector.source_name}...")
                items = connector.fetch_new_items()
                
                new_count = 0
                for raw_item in items:
                    parsed_data = connector.parse_item(raw_item)
                    if database.save_resource(connector.source_name, parsed_data):
                        new_count += 1
                
                logging.info(f"✨ {connector.source_name} : {new_count} ressources traitées.")
                
            except Exception as e:
                logging.error(f"❌ Erreur lors de la synchro de {connector.source_name} : {e}")
        
        logging.info("🏁 Cycle de synchronisation terminé.")

def run_orchestrator_daemon():
    """Démon qui synchronise les sources OSINT périodiquement (toutes les 6 heures)."""
    orchestrator = CyberOrchestrator()
    while True:
        try:
            orchestrator.run_sync_cycle()
            logging.info("😴 Orchestrateur en sommeil pour 6 heures...")
            time.sleep(6 * 3600)
        except Exception as e:
            logging.error(f"❌ Erreur critique orchestrateur : {e}")
            time.sleep(300)

if __name__ == "__main__":
    # Test immédiat
    orchestrator = CyberOrchestrator()
    orchestrator.run_sync_cycle()
