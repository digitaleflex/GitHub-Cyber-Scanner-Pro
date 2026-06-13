# 🌐 Architecture de Veille OSINT - Méta-Moteur SearXNG

Ce document décrit l'intégration d'un méta-moteur de recherche open-source (SearXNG) pour étendre les capacités du Cyber Scanner en dehors de GitHub, afin de trouver des ressources rares (PDF, rapports d'audit, PoC) via le Google Dorking.

## 1. Intégration Docker (SearXNG)

Pour éviter les blocages d'IP et les Captchas de Google, le développeur doit ajouter un conteneur SearXNG dans l'architecture locale.

```yaml
  # Dans compose.yml
  searxng:
    image: searxng/searxng:latest
    container_name: cyber_searxng
    restart: always
    ports:
      - "8080:8080"
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
      - SEARXNG_SECRET=cyber_secret_key
    volumes:
      - ./searxng:/etc/searxng
```

## 2. Générateur de Dorks (Python)

Le développeur doit implémenter un générateur automatique de Dorks pour cibler précisément les types de fichiers recherchés.

```python
# src/osint_dorker.py

def generate_osint_dork(keyword, resource_type="pdf"):
    """
    Génère des Google Dorks professionnels selon la typologie de ressource.
    """
    if resource_type == "pdf":
        return f'"{keyword}" filetype:pdf intitle:"index of"'
    elif resource_type == "report":
        return f'"{keyword}" filetype:pdf "penetration test report"'
    elif resource_type == "exploit":
        return f'site:pastebin.com "{keyword}" (RCE OR exploit OR payload)'
    return f'"{keyword}"'
```

## 3. Typologie des Recherches OSINT

* **Manuels Universitaires** : `"cybersecurity" filetype:pdf (inurl:edu OR inurl:org) "course" OR "lecture"`
* **E-Books non protégés** : `intitle:"index of" "cybersecurity" OR "hacking" filetype:pdf`
* **Rapports de Pentest réels** : `filetype:pdf "penetration test report" -site:github.com`
* **Preuves de Concept (PoC)** : `site:pastebin.com "remote code execution" OR "exploit"`
