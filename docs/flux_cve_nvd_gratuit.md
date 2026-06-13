# 🔓 Veille CVE/NVD Gratuite - Stratégie 100% Locale & Open Source

Ce document explique comment le scanner intègre les bases de données mondiales de vulnérabilités **sans aucune API payante**, en s'appuyant sur les flux publics gouvernementaux et les bases embarquées de Trivy.

---

## 1. Les Sources Officielles Gratuites (CVE / NVD)

Toute faille officielle reçoit un identifiant unique mondial appelé **CVE** (Common Vulnerabilities and Exposures). Ces failles sont centralisées dans la **NVD** (National Vulnerability Database) publiée par le gouvernement américain via le NIST.

### Flux de données disponibles gratuitement

| Source | Format | Mise à jour | URL de téléchargement |
|--------|--------|-------------|----------------------|
| NVD (NIST) | JSON compressé (.gz) | Quotidienne | `https://nvd.nist.gov/feeds/json/cve/1.1/` |
| GHSA (GitHub) | JSON via API REST publique | Temps réel | `https://api.github.com/advisories` |
| OSV.dev (Google) | JSON agrégé multi-langages | Temps réel | `https://api.osv.dev/v1/query` |

### Implémentation dans le scanner Python

```python
# src/cve_updater.py
import requests, gzip, json, os

NVD_FEED_URL = "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz"
LOCAL_CACHE_PATH = "/app/data/nvd_recent.json"

def download_nvd_feed():
    """Télécharge et met à jour le flux NVD quotidien (gratuit, aucune clé requise)."""
    response = requests.get(NVD_FEED_URL, stream=True, timeout=60)
    with gzip.open(response.raw, "rb") as f:
        data = json.load(f)
    with open(LOCAL_CACHE_PATH, "w") as out:
        json.dump(data, out)
    print(f"[NVD] {len(data['CVE_Items'])} CVE mises a jour localement.")
    return data

def check_dependency_against_nvd(package_name, version):
    """Verifie si un package/version est connu comme vulnerable dans le cache NVD local."""
    if not os.path.exists(LOCAL_CACHE_PATH):
        download_nvd_feed()
    with open(LOCAL_CACHE_PATH) as f:
        data = json.load(f)
    # Recherche par nom de composant (simplifiée)
    matches = [
        item["cve"]["CVE_data_meta"]["ID"]
        for item in data["CVE_Items"]
        if package_name.lower() in str(item).lower()
    ]
    return matches
```

---

## 2. Trivy : L'Agrégateur Automatique (Sans Configuration Manuelle)

Le conteneur Trivy agrège **automatiquement et gratuitement** plusieurs bases de vulnérabilités à chaque démarrage :

| Base de données | Couverture |
|-----------------|-----------|
| NVD (NIST) | Toutes les CVE officielles |
| GHSA (GitHub) | Vulnérabilités des dépendances (npm, PyPI, Go) |
| OSV (Google) | Open Source Vulnerabilities (multi-langages) |
| RedHat RHSA | Alertes Linux RedHat/CentOS |
| Debian / Ubuntu | Alertes des paquets OS Debian |

> **Le principe clé :** Trivy stocke ces bases dans un **cache local** (`~/.cache/trivy`). Après la première mise à jour, tous les scans se font à la vitesse de l'éclair, entièrement hors-ligne.

### Intégration dans le workflow du scanner (Docker-in-Docker)

```python
# Dans src/scanner.py - Workflow SAST éphémère sécurisé
import subprocess, tempfile, shutil

def audit_repository(repo_url: str) -> dict:
    """
    Clone partiellement un depot, lance Trivy, puis supprime immediatement.
    Aucune cle API requise. Toutes les CVE sont verifiees localement.
    """
    temp_dir = tempfile.mkdtemp(prefix="cyber_scan_")
    try:
        # 1. Clone leger (sans historique git pour economiser l'espace disque)
        subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", repo_url, temp_dir],
            check=True, timeout=60
        )
        # 2. Scan Trivy local (bases CVE telechargees automatiquement par Trivy)
        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{temp_dir}:/app",
            "-v", "trivy-cache:/root/.cache/",  # Cache persistent entre les scans
            "aquasec/trivy:latest", "fs", "/app",
            "--format", "json", "--quiet"
        ], capture_output=True, text=True, timeout=120)
        return result.stdout
    finally:
        # 3. Nettoyage immediat pour eviter la saturation disque
        shutil.rmtree(temp_dir, ignore_errors=True)
```

---

## 3. Veille 0-Day via SearXNG (L'Avantage Concurrentiel)

Les failles **Zero-Day** sont exploitées par les hackers **avant** d'avoir un numéro CVE officiel. Notre moteur les détecte en avant-première grâce au dorking autonome via SearXNG.

### Sources cibles des Dorks 0-Day

```python
# src/osint_dorker.py - Génération des dorks de veille 0-Day
ZERO_DAY_DORK_TEMPLATES = [
    # Exploit-DB : Base de données d'exploits publics référencée
    'site:exploit-db.com "{keyword}"',
    # Packet Storm Security : Alertes et PoC publiés par des chercheurs
    'site:packetstormsecurity.com "proof of concept" "{keyword}"',
    # GitHub Gists : PoC publiés rapidement par les chercheurs
    'site:gist.github.com "RCE" OR "remote code execution" "{keyword}"',
    # Rapports de divulgation coordonnée
    'site:seclists.org "{keyword}" "exploit" filetype:txt',
]

def generate_zeroday_dork(keyword):
    """Génère des requêtes de surveillance pour détecter les nouveaux exploits 0-Day."""
    return [template.format(keyword=keyword) for template in ZERO_DAY_DORK_TEMPLATES]
```

### Flux de détection automatique

```
SearXNG (Local) → Dork 0-Day → Résultats Web
       ↓
  NLP Local (IA) → Détection : "PoC", "RCE", "exploit"
       ↓
  Qdrant → Indexation immédiate avec tag "zero_day_candidate"
       ↓
  Dashboard → Badge "Alerte Threat" visible sur la ressource
```

> **Avantage commercial :** Votre moteur peut détecter et alerter sur un Zero-Day **plusieurs jours avant** que NVD lui attribue un CVE officiel. C'est le cœur de l'offre **PRO** (alertes en temps réel).

---

## 4. Résumé : Stratégie Zéro-Coût, Maximum d'Intelligence

| Besoin | Solution | Coût |
|--------|----------|------|
| CVE officielles à jour | Flux NVD/GHSA/OSV via Trivy | 0€ |
| Scan des dépendances | Trivy local (cache persistent) | 0€ |
| Détection 0-Day précoce | SearXNG + Dorking Exploit-DB/PacketStorm | 0€ |
| Alertes temps réel (PRO) | NLP local (MiniLM) + Qdrant tag | 0€ |
