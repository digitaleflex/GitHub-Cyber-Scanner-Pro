# Spécifications - Connecteurs de Cybersécurité (Vague 2)

**Date :** 2024-05-24
**Auteur :** Gemini CLI Agent
**Statut :** Approuvé (Auto-validation en mode non-interactif)

## 1. Objectif
Implémenter 4 nouveaux connecteurs pour le système de scan de ressources de cybersécurité. Ces connecteurs doivent être robustes, furtifs et retourner des données au format standard.

## 2. Sources à implémenter

| Source | Type de ressource | Méthode | URL de base |
| :--- | :--- | :--- | :--- |
| **Packet Storm** | Outil / Bulletin | RSS | `https://packetstormsecurity.com/feeds/` |
| **Codeberg** | Code / Outil | API JSON | `https://codeberg.org/api/v1/repos/search` |
| **0day.today** | PoC / Exploit | RSS / Scraper | `https://0day.today/rss/en` |
| **CXSecurity** | Vulnérabilité / Advisory | RSS | `https://cxsecurity.com/wivuv/rss/` |

## 3. Architecture Technique

### 3.1 Classe de base
Tous les connecteurs hériteront de `BaseConnector` (`src/connectors/base_connector.py`).

### 3.2 Format de sortie standard
Chaque item retourné par `parse_item` doit suivre ce schéma :
```python
{
    "external_id": str,      # Préfixe source + ID unique (ex: PS-123)
    "title": str,           # Titre de la ressource
    "description": str,     # Résumé ou description (tronqué si nécessaire)
    "url": str,             # URL de la page de détail
    "raw_content_url": str, # URL vers le contenu brut (si disponible)
    "type_ressource": str,  # Catégorie (Livre, PoC / Exploit, etc.)
    "language": str,        # Code langue (fr, en, etc.)
    "discovered_at": datetime
}
```

### 3.3 Furtivité (Stealth)
- Utilisation systématique de `self.stealth_get()` pour les requêtes.
- Respect des User-Agents modernes.
- Gestion des délais et des timeouts.

## 4. Détails par connecteur

### 4.1 PacketStormConnector
- Utilise `xml.etree.ElementTree` pour parser le flux RSS.
- `external_id` extrait de l'URL ou du GUID.

### 4.2 CodebergConnector
- Recherche par mots-clés (`security`, `exploit`, `cybersecurity`).
- Tri par `updated` décroissant.
- Conversion du format JSON de l'API Codeberg vers le format standard.

### 4.3 ZerodayConnector
- Parser de flux RSS.
- Gestion robuste des erreurs si Cloudflare bloque l'accès (retourner une liste vide avec log d'erreur).

### 4.4 CXSecurityConnector
- Parser de flux RSS standard.
- Extraction des bulletins de sécurité mondiaux.

## 5. Validation
- Chaque connecteur inclura un bloc de test `if __name__ == "__main__":`.
- Vérification de la conformité du format de sortie.
- Tests de robustesse (simulations de pannes réseau).
