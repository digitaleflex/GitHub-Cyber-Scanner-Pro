"""Proxy manager — SOCKS5 via Tor pour débloquer les requêtes sortantes."""
import logging
import os
import socket

import requests

TOR_HOST = os.getenv("TOR_PROXY_HOST", "127.0.0.1")
TOR_PORT = int(os.getenv("TOR_PROXY_PORT", "9050"))
TOR_ENABLED = os.getenv("TOR_ENABLED", "true").lower() == "true"

# Pour utiliser Tor depuis le conteneur Docker (host network)
# Le conteneur doit avoir --network=host ou le port Tor doit être exposé


def get_proxies() -> dict:
    """Retourne les proxies SOCKS5 si Tor est dispo."""
    if not TOR_ENABLED:
        return {}
    try:
        s = socket.create_connection((TOR_HOST, TOR_PORT), timeout=2)
        s.close()
        return {"http": f"socks5h://{TOR_HOST}:{TOR_PORT}",
                "https": f"socks5h://{TOR_HOST}:{TOR_PORT}"}
    except Exception:
        return {}


def get_session(use_proxy: bool = True) -> requests.Session:
    """Crée une session requests avec proxy Tor si dispo."""
    session = requests.Session()
    if use_proxy and TOR_ENABLED:
        proxies = get_proxies()
        if proxies:
            session.proxies.update(proxies)
            logging.debug("Session avec proxy Tor activee")
    return session


def tor_status() -> dict:
    """Vérifie si Tor est disponible."""
    try:
        s = socket.create_connection((TOR_HOST, TOR_PORT), timeout=3)
        s.close()
        return {"available": True, "host": TOR_HOST, "port": TOR_PORT}
    except Exception:
        return {"available": False, "host": TOR_HOST, "port": TOR_PORT,
                "error": "Connexion refusee — Tor n'est pas lance"}
