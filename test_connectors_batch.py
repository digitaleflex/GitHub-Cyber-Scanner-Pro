import sys
import os
import logging

# Ajouter le chemin racine au sys.path
sys.path.append(os.getcwd())

from src.connectors.packetstorm_connector import PacketStormConnector
from src.connectors.codeberg_connector import CodebergConnector
from src.connectors.zeroday_connector import ZeroDayConnector
from src.connectors.cxsecurity_connector import CXSecurityConnector

logging.basicConfig(level=logging.INFO)

def test_connector(connector_class):
    print(f"\n--- Testing {connector_class.__name__} ---")
    try:
        connector = connector_class()
        items = connector.fetch_new_items()
        if items:
            print(f"✅ Success: {len(items)} items found.")
            parsed = connector.parse_item(items[0])
            print(f"Sample item: {parsed}")
        else:
            print("❌ Failure: No items found.")
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    test_connector(PacketStormConnector)
    test_connector(CodebergConnector)
    test_connector(ZeroDayConnector)
    test_connector(CXSecurityConnector)
