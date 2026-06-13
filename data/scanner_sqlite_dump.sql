-- ==========================================
-- 🚀 SCRIPT D'INITIALISATION POSTGRESQL
-- PROJET : GITHUB CYBER SCANNER PRO (MVP)
-- ==========================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. TABLES DES DÉPÔTS (CORE)
CREATE TABLE IF NOT EXISTS repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) UNIQUE NOT NULL,
    html_url TEXT NOT NULL,
    description TEXT,
    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    language VARCHAR(50),
    topics TEXT[],
    license VARCHAR(100),
    pushed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Métadonnées OSINT & NLP
    extracted_keywords TEXT[],
    summary_ai TEXT, -- Le résumé de 3 lignes généré par Ollama
    category_cyber VARCHAR(100), -- Catégorie détectée (RedTeam, BlueTeam, etc.)
    
    -- Scores & Vitalité
    quality_score INTEGER DEFAULT 0, -- Score de 0 à 100
    vitality_score INTEGER DEFAULT 0, -- Score de maintenance
    is_obsolete BOOLEAN DEFAULT FALSE,
    is_hot_trend BOOLEAN DEFAULT FALSE,
    
    -- Stockage JSONB pour la flexibilité (Résultats bruts API/SearXNG)
    raw_metadata JSONB
);

-- 3. LOGS DE SÉCURITÉ (AUDIT SAST)
CREATE TABLE IF NOT EXISTS security_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    scan_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Résultats Trivy (Vulnerabilités de dépendances)
    trivy_status VARCHAR(20), -- (Clean, Suspect, Critical)
    trivy_report JSONB,
    
    -- Résultats Semgrep (SAST)
    semgrep_status VARCHAR(20),
    semgrep_report JSONB,
    
    -- Résultats Gitleaks (Secrets)
    gitleaks_found BOOLEAN DEFAULT FALSE,
    gitleaks_report JSONB,
    
    -- Score de confiance calculé
    trust_score INTEGER DEFAULT 0
);

-- 4. GESTION DES RECHERCHES ET UTILISATEURS
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    subscription_tier VARCHAR(20) DEFAULT 'FREE', -- (FREE, PRO, ENTERPRISE)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    search_type VARCHAR(20), -- (Semantic, Keyword)
    results_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. INDEXATION POUR LA PERFORMANCE
CREATE INDEX idx_repo_full_name ON repositories(full_name);
CREATE INDEX idx_repo_quality_score ON repositories(quality_score);
CREATE INDEX idx_repo_category ON repositories(category_cyber);
CREATE INDEX idx_repo_jsonb_data ON repositories USING GIN (raw_metadata);
CREATE INDEX idx_security_repo_id ON security_scans(repository_id);

-- 6. TRIGGERS POUR UPDATED_AT
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_repositories_updated_at
    BEFORE UPDATE ON repositories
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();
