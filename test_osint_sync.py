import os
import sys
import logging

# Ajouter src au path pour les imports
sys.path.append(os.path.join(os.getcwd(), 'src'))

import database
from orchestrator import CyberOrchestrator

def run_test_sync():
    logging.info("🧪 Démarrage d'une synchronisation de test (Exploit-DB & CISA-KEV)...")
    
    # Initialiser la DB si besoin (pour créer les nouvelles tables)
    database.init_db()
    
    orchestrator = CyberOrchestrator()
    
    # Filtrer pour ne tester que 2 connecteurs rapides pour la démo
    test_connectors = [c for connector in orchestrator.connectors if (c := connector).source_name in ["Exploit-DB", "CISA-KEV"]]
    
    if not test_connectors:
        # Si le chargement dynamique n'a pas encore pris (car on est hors docker)
        from connectors.exploitdb_connector import ExploitDBConnector
        from connectors.cisakev_connector import CisaKevConnector
        test_connectors = [ExploitDBConnector(), CisaKevConnector()]

    for connector in test_connectors:
        try:
            logging.info(f"📡 Test Synchro : {connector.source_name}...")
            items = connector.fetch_new_items()
            
            # On n'en traite que 10 pour le test
            new_count = 0
            for raw_item in items[:10]:
                parsed_data = connector.parse_item(raw_item)
                if database.save_resource(connector.source_name, parsed_data):
                    new_count += 1
            
            logging.info(f"✅ {connector.source_name} : {new_count} ressources injectées avec succès.")
            
        except Exception as e:
            logging.error(f"❌ Erreur test {connector.source_name} : {e}")

    logging.info("🏁 Test terminé. Les données devraient être visibles sur http://localhost:8000/api/resources")

if __name__ == "__main__":
    run_test_sync()
