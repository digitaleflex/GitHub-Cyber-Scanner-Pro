-- Schéma de base de données souverain pour Cyber Intelligence Platform
-- Supporte GitHub, GitLab, arXiv, NIST, Exploit-DB, etc.

-- Extension pour la recherche vectorielle (si non activée)
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Table des sources de données (Les 20 sources stratégiques)
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    url VARCHAR(500),
    type VARCHAR(50), -- 'Academique', 'OSINT', 'Exploit', 'Threat-Intel'
    is_active BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP
);

-- 2. Table universelle des ressources
CREATE TABLE IF NOT EXISTS resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id INTEGER REFERENCES sources(id),
    external_id VARCHAR(255), -- ID original dans la source (ex: CVE-ID, arXiv-ID)
    title TEXT NOT NULL,
    description TEXT,
    content_raw TEXT, -- Texte complet extrait (PDF ou README)
    url VARCHAR(1000) UNIQUE NOT NULL,
    type_ressource VARCHAR(100), -- 'PDF', 'PoC', 'Script', 'Report'
    language VARCHAR(10) DEFAULT 'en',
    
    -- Métriques IA
    score_qualite INTEGER DEFAULT 0,
    security_verdict VARCHAR(20) DEFAULT 'NON_AUDITE',
    
    -- Recherche Sémantique & Vectorielle
    vecteur_semantique vector(384),
    tsv_content tsvector,
    
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- 3. Table des Chunks (Pour le RAG et Qdrant)
-- Découpage des gros PDF en blocs de 1000 caractères
CREATE TABLE IF NOT EXISTS resource_chunks (
    id SERIAL PRIMARY KEY,
    resource_id UUID REFERENCES resources(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    content_text TEXT,
    embedding vector(384)
);

-- 4. Table spécifique aux Vulnérabilités & Exploits (Corrélation)
CREATE TABLE IF NOT EXISTS security_intel (
    id SERIAL PRIMARY KEY,
    resource_id UUID REFERENCES resources(id) ON DELETE CASCADE,
    cve_id VARCHAR(50),
    severity VARCHAR(20),
    exploit_available BOOLEAN DEFAULT FALSE,
    patch_available BOOLEAN DEFAULT FALSE
);

-- Indexation GIN pour la recherche plein texte rapide
CREATE INDEX IF NOT EXISTS resources_tsv_idx ON resources USING GIN (tsv_content);

-- Insertion des 5 premières sources prioritaires
INSERT INTO sources (name, url, type) VALUES 
('Internet Archive', 'https://archive.org', 'Academique'),
('arXiv cs.CR', 'https://arxiv.org/list/cs.CR/recent', 'Academique'),
('NIST CSRC', 'https://csrc.nist.gov', 'Institutionnel'),
('Exploit-DB', 'https://www.exploit-db.com', 'Exploit'),
('CISA KEV', 'https://www.cisa.gov/known-exploited-vulnerabilities-catalog', 'Threat-Intel')
ON CONFLICT (name) DO NOTHING;
