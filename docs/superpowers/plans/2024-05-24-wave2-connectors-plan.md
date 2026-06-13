# Plan d'implémentation - Connecteurs de Cybersécurité (Vague 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implémenter 4 connecteurs Python robustes et furtifs pour Packet Storm, Codeberg, 0day.today et CXSecurity.

**Architecture:** Chaque connecteur hérite de `BaseConnector` et implémente le cycle `fetch_new_items` -> `parse_item`.

**Tech Stack:** Python 3.x, `requests`, `xml.etree.ElementTree`, `json`.

---

### Task 1: PacketStormConnector

**Files:**
- Create: `src/connectors/packetstorm_connector.py`

- [ ] **Step 1: Implémenter le squelette de PacketStormConnector**
  Hériter de `BaseConnector` et définir `RSS_URL = "https://packetstormsecurity.com/feeds/all/"`.

- [ ] **Step 2: Implémenter `fetch_new_items`**
  Utiliser `stealth_get` et `xml.etree.ElementTree` pour parser le flux.

- [ ] **Step 3: Implémenter `parse_item`**
  Extraire le titre, le lien, la description et générer un `external_id` de type `PS-<id>`.

- [ ] **Step 4: Ajouter le bloc de test `if __name__ == "__main__":`**
  Vérifier que le connecteur peut récupérer au moins un item et l'afficher au format standard.

---

### Task 2: CodebergConnector

**Files:**
- Create: `src/connectors/codeberg_connector.py`

- [ ] **Step 1: Implémenter le squelette de CodebergConnector**
  Hériter de `BaseConnector` et définir `API_URL = "https://codeberg.org/api/v1/repos/search"`.

- [ ] **Step 2: Implémenter `fetch_new_items`**
  Utiliser `stealth_get` avec les paramètres `q=security`, `sort=updated`, `order=desc`.

- [ ] **Step 3: Implémenter `parse_item`**
  Mapper les champs JSON de Codeberg vers le format standard. `external_id` : `CB-<repo_id>`.

- [ ] **Step 4: Ajouter le bloc de test `if __name__ == "__main__":`**
  Tester avec un mot-clé comme "security" ou "exploit".

---

### Task 3: ZerodayConnector

**Files:**
- Create: `src/connectors/zeroday_connector.py`

- [ ] **Step 1: Implémenter le squelette de ZerodayConnector**
  Hériter de `BaseConnector` et définir `RSS_URL = "https://0day.today/rss/en"`.

- [ ] **Step 2: Implémenter `fetch_new_items`**
  Utiliser `stealth_get` et gérer les cas de blocage Cloudflare (403) gracieusement.

- [ ] **Step 3: Implémenter `parse_item`**
  Extraire les métadonnées de l'exploit. `external_id` : `0DAY-<id>`.

- [ ] **Step 4: Ajouter le bloc de test `if __name__ == "__main__":`**
  Vérifier si le flux est accessible et si le parsing fonctionne.

---

### Task 4: CXSecurityConnector

**Files:**
- Create: `src/connectors/cxsecurity_connector.py`

- [ ] **Step 1: Implémenter le squelette de CXSecurityConnector**
  Hériter de `BaseConnector` et définir `RSS_URL = "https://cxsecurity.com/wivuv/rss/"`.

- [ ] **Step 2: Implémenter `fetch_new_items`**
  Utiliser `stealth_get` et `xml.etree.ElementTree`.

- [ ] **Step 3: Implémenter `parse_item`**
  Mapper les champs du flux vers le format standard. `external_id` : `CX-<id>`.

- [ ] **Step 4: Ajouter le bloc de test `if __name__ == "__main__":`**
  Tester la récupération des dernières vulnérabilités.

---

### Task 5: Intégration et Validation Finale

- [ ] **Step 1: Vérifier la cohérence des types de ressources**
  S'assurer que les connecteurs utilisent des termes cohérents : "Outil / Bulletin", "Code / Outil", "PoC / Exploit", "Vulnérabilité / Advisory".

- [ ] **Step 2: Test d'import global**
  Vérifier que tous les connecteurs peuvent être importés sans erreur depuis `src/main.py` ou un script de test.
