import logging
import src.db.connection as _conn



def init_db():
    conn = _conn.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            id VARCHAR(50) PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            stars INTEGER,
            description TEXT,
            html_url VARCHAR(500),
            language VARCHAR(100),
            updated_at VARCHAR(100),
            readme_parsed INTEGER DEFAULT 0,
            security_verdict VARCHAR(20),
            security_details TEXT,
            security_scan_date TIMESTAMP,
            embedding vector(384),
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'security_verdict'
            ) THEN
                ALTER TABLE repositories ADD COLUMN security_verdict VARCHAR(20);
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'security_details'
            ) THEN
                ALTER TABLE repositories ADD COLUMN security_details TEXT;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'security_scan_date'
            ) THEN
                ALTER TABLE repositories ADD COLUMN security_scan_date TIMESTAMP;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'vitality_score'
            ) THEN
                ALTER TABLE repositories ADD COLUMN vitality_score INTEGER DEFAULT 0;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'semantic_category'
            ) THEN
                ALTER TABLE repositories ADD COLUMN semantic_category VARCHAR(30);
            END IF;
        END $$;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            repo_id VARCHAR(50) REFERENCES repositories(id) ON DELETE CASCADE,
            title VARCHAR(500) NOT NULL,
            url VARCHAR(1000) UNIQUE NOT NULL,
            category VARCHAR(150),
            is_dead INTEGER DEFAULT 0,
            last_checked TIMESTAMP,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'books' AND column_name = 'lemmas_str'
            ) THEN
                ALTER TABLE books ADD COLUMN lemmas_str TEXT;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'books' AND column_name = 'score_qualite'
            ) THEN
                ALTER TABLE books ADD COLUMN score_qualite INTEGER DEFAULT 0;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'books' AND column_name = 'type_ressource'
            ) THEN
                ALTER TABLE books ADD COLUMN type_ressource VARCHAR(50) DEFAULT 'link';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'books' AND column_name = 'tsv_content'
            ) THEN
                ALTER TABLE books ADD COLUMN tsv_content TSVECTOR;
            END IF;
        END $$;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etag_cache (
            query VARCHAR(500) PRIMARY KEY,
            etag VARCHAR(500),
            last_modified VARCHAR(500),
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discovered_keywords (
            id SERIAL PRIMARY KEY,
            term VARCHAR(150) UNIQUE NOT NULL,
            category_guess VARCHAR(30),
            score FLOAT DEFAULT 0,
            sources INTEGER DEFAULT 0,
            source_samples TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repo_issues (
            id BIGSERIAL PRIMARY KEY,
            repo_id VARCHAR(50) REFERENCES repositories(id) ON DELETE CASCADE,
            issue_number INTEGER,
            title TEXT,
            body TEXT,
            state VARCHAR(20),
            labels TEXT,
            author VARCHAR(100),
            created_at VARCHAR(100),
            updated_at VARCHAR(100),
            html_url VARCHAR(500),
            is_security BOOLEAN DEFAULT FALSE,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(repo_id, issue_number)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repo_commits (
            id BIGSERIAL PRIMARY KEY,
            repo_id VARCHAR(50) REFERENCES repositories(id) ON DELETE CASCADE,
            sha VARCHAR(64),
            message TEXT,
            author VARCHAR(100),
            date VARCHAR(100),
            html_url VARCHAR(500),
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(repo_id, sha)
        )
    """)

    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'issues_harvested'
            ) THEN
                ALTER TABLE repositories ADD COLUMN issues_harvested INTEGER DEFAULT 0;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'commits_harvested'
            ) THEN
                ALTER TABLE repositories ADD COLUMN commits_harvested INTEGER DEFAULT 0;
            END IF;
        END $$;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cve_entries (
            id SERIAL PRIMARY KEY,
            cve_id VARCHAR(30) UNIQUE NOT NULL,
            description TEXT,
            published DATE,
            last_modified DATE,
            severity VARCHAR(20),
            cvss_score FLOAT,
            references_urls TEXT,
            weaknesses TEXT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration: chunks de README lies aux repos (RAG) + colonnes repo_id/chunk_type
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'resource_chunks' AND column_name = 'repo_id'
            ) THEN
                ALTER TABLE resource_chunks ADD COLUMN repo_id VARCHAR(50);
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'resource_chunks' AND column_name = 'chunk_type'
            ) THEN
                ALTER TABLE resource_chunks ADD COLUMN chunk_type VARCHAR(30);
            END IF;
        END $$;
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_repo ON resource_chunks (repo_id, chunk_type)")

    # Indexation GIN trigramme pour les recherches ILIKE %...% sur gros volumes
    cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_repos_name_trgm ON repositories USING gin (full_name gin_trgm_ops)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_repos_desc_trgm ON repositories USING gin (description gin_trgm_ops)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_repos_lang_trgm ON repositories USING gin (language gin_trgm_ops)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cves_id_trgm ON cve_entries USING gin (cve_id gin_trgm_ops)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cves_desc_trgm ON cve_entries USING gin (description gin_trgm_ops)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_title_trgm ON books USING gin (title gin_trgm_ops)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords_term_trgm ON discovered_keywords USING gin (term gin_trgm_ops)")

    # Migration: ajout colonne embedding pour la recherche semantique
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'embedding'
            ) THEN
                ALTER TABLE repositories ADD COLUMN embedding vector(384);
            END IF;
        END $$;
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_repos_embedding ON repositories USING ivfflat (embedding vector_cosine_ops)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            sector VARCHAR(100),
            compliance_frameworks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asset_inventory (
            id SERIAL PRIMARY KEY,
            org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            asset_type VARCHAR(30) NOT NULL,
            name VARCHAR(200) NOT NULL,
            vendor VARCHAR(200),
            version VARCHAR(50),
            exposed BOOLEAN DEFAULT false,
            criticality SMALLINT DEFAULT 3 CHECK (criticality BETWEEN 1 AND 5),
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_org ON asset_inventory (org_id, asset_type)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            org_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'non_defini',
            display_name VARCHAR(200),
            preferences JSONB DEFAULT '{}',
            onboarding_completed BOOLEAN DEFAULT false,
            last_active TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_org ON user_profiles (org_id)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS epss_scores (
            cve_id VARCHAR(30) PRIMARY KEY REFERENCES cve_entries(cve_id) ON DELETE CASCADE,
            epss FLOAT NOT NULL,
            percentile FLOAT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_epss_score ON epss_scores (epss DESC)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS missions (
            id SERIAL PRIMARY KEY,
            org_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
            title VARCHAR(300) NOT NULL,
            description TEXT,
            objective TEXT,
            status VARCHAR(20) DEFAULT 'active',
            progress INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
            estimated_minutes INTEGER,
            risk_reduction_percent INTEGER CHECK (risk_reduction_percent BETWEEN -100 AND 100),
            cve_ids TEXT,
            responsible VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_missions_org_status ON missions (org_id, status)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mission_steps (
            id SERIAL PRIMARY KEY,
            mission_id INTEGER REFERENCES missions(id) ON DELETE CASCADE,
            step_order INTEGER NOT NULL,
            title VARCHAR(300) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            action_type VARCHAR(50),
            estimated_minutes INTEGER,
            completed_at TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mission_steps ON mission_steps (mission_id, step_order)")

    # ── Cycle de vie des vulnerabilites ──────────────────────────────────────
    # Exploits (Exploit-DB importes par exploit_loader.py, requis par api_routes/correlation)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exploits (
            exploit_id VARCHAR(50) PRIMARY KEY,
            description TEXT,
            platform VARCHAR(100),
            exploit_type VARCHAR(100),
            author VARCHAR(200),
            date VARCHAR(20),
            file_url VARCHAR(500),
            cve_id VARCHAR(30),
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exploits_cve ON exploits (cve_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exploits_platform ON exploits (platform)")
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'exploits' AND column_name = 'cve_id'
            ) THEN
                ALTER TABLE exploits ADD COLUMN cve_id VARCHAR(30);
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'exploits' AND column_name = 'discovered_at'
            ) THEN
                ALTER TABLE exploits ADD COLUMN discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            END IF;
        END $$;
    """)

    # CISA KEV dedie (champs officiels, degorge le marqueur dans weaknesses)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cve_kev (
            cve_id VARCHAR(30) PRIMARY KEY REFERENCES cve_entries(cve_id) ON DELETE CASCADE,
            vulnerability_name VARCHAR(500),
            cisa_kev_date DATE,
            due_date DATE,
            required_action TEXT,
            ransomware_campaign VARCHAR(100),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # IOC Feed (IP, domaines, hashes, URLs, emails) + pont vers les CVE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ioc_feed (
            id SERIAL PRIMARY KEY,
            source VARCHAR(50) NOT NULL,
            value TEXT NOT NULL,
            ioc_type VARCHAR(30) NOT NULL,
            threat_type VARCHAR(200),
            tags TEXT,
            first_seen TIMESTAMP,
            status VARCHAR(30) DEFAULT 'active',
            raw_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(value)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ioc_source ON ioc_feed(source)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ioc_type ON ioc_feed(ioc_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ioc_first_seen ON ioc_feed(first_seen)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cve_iocs (
            cve_id VARCHAR(30) REFERENCES cve_entries(cve_id) ON DELETE CASCADE,
            ioc_id INTEGER REFERENCES ioc_feed(id) ON DELETE CASCADE,
            confidence SMALLINT DEFAULT 3 CHECK (confidence BETWEEN 1 AND 5),
            PRIMARY KEY (cve_id, ioc_id)
        )
    """)

    # Regles de detection : Sigma, YARA, Suricata/Snort
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sigma_rules (
            id SERIAL PRIMARY KEY,
            rule_id VARCHAR(200),
            title TEXT NOT NULL,
            description TEXT,
            level VARCHAR(20),
            status VARCHAR(30),
            tags TEXT,
            logsource TEXT,
            detection TEXT,
            source VARCHAR(100),
            file_url VARCHAR(500),
            cve_id VARCHAR(30),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(rule_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sigma_cve ON sigma_rules (cve_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sigma_level ON sigma_rules (level)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS yara_rules (
            id SERIAL PRIMARY KEY,
            rule_name VARCHAR(200),
            title TEXT,
            author VARCHAR(200),
            description TEXT,
            tags TEXT,
            rule_text TEXT NOT NULL,
            source VARCHAR(100),
            file_url VARCHAR(500),
            cve_id VARCHAR(30),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(rule_name)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_yara_cve ON yara_rules (cve_id)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ids_rules (
            id SERIAL PRIMARY KEY,
            engine VARCHAR(20) NOT NULL,
            sid INTEGER,
            gid INTEGER,
            rev INTEGER,
            message TEXT,
            severity SMALLINT DEFAULT 3,
            priority SMALLINT DEFAULT 3,
            reference TEXT,
            rule_text TEXT NOT NULL,
            source VARCHAR(100),
            file_url VARCHAR(500),
            cve_id VARCHAR(30),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(engine, sid)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ids_cve ON ids_rules (cve_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ids_engine ON ids_rules (engine)")

    # ATT&CK techniques (MITRE) + mapping CVE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attack_techniques (
            id SERIAL PRIMARY KEY,
            technique_id VARCHAR(30) UNIQUE NOT NULL,
            name VARCHAR(300) NOT NULL,
            tactic VARCHAR(200),
            platform VARCHAR(100),
            description TEXT,
            url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attack_tactic ON attack_techniques (tactic)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cve_attack_mapping (
            cve_id VARCHAR(30) REFERENCES cve_entries(cve_id) ON DELETE CASCADE,
            technique_id VARCHAR(30) REFERENCES attack_techniques(technique_id) ON DELETE CASCADE,
            confidence SMALLINT DEFAULT 3 CHECK (confidence BETWEEN 1 AND 5),
            PRIMARY KEY (cve_id, technique_id)
        )
    """)

    # CAPEC patterns (MITRE) + mapping CVE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS capec_patterns (
            id SERIAL PRIMARY KEY,
            capec_id VARCHAR(30) UNIQUE NOT NULL,
            name VARCHAR(300) NOT NULL,
            description TEXT,
            likelihood VARCHAR(50),
            severity VARCHAR(50),
            prerequisites TEXT,
            url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cve_capec_mapping (
            cve_id VARCHAR(30) REFERENCES cve_entries(cve_id) ON DELETE CASCADE,
            capec_id VARCHAR(30) REFERENCES capec_patterns(capec_id) ON DELETE CASCADE,
            PRIMARY KEY (cve_id, capec_id)
        )
    """)

    # Acteurs (APT) et campagnes + mapping CVE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apt_groups (
            id SERIAL PRIMARY KEY,
            name VARCHAR(300) UNIQUE NOT NULL,
            aliases TEXT,
            description TEXT,
            motivations TEXT,
            countries TEXT,
            first_seen DATE,
            tools TEXT,
            url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id SERIAL PRIMARY KEY,
            name VARCHAR(300) NOT NULL,
            description TEXT,
            threat_actor_id INTEGER REFERENCES apt_groups(id) ON DELETE SET NULL,
            status VARCHAR(30) DEFAULT 'active',
            target_sectors TEXT,
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns (status)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cve_campaign_mapping (
            cve_id VARCHAR(30) REFERENCES cve_entries(cve_id) ON DELETE CASCADE,
            campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
            PRIMARY KEY (cve_id, campaign_id)
        )
    """)

    # Produits affectes (CPE) et correctifs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cve_affected_products (
            id SERIAL PRIMARY KEY,
            cve_id VARCHAR(30) REFERENCES cve_entries(cve_id) ON DELETE CASCADE,
            product VARCHAR(300) NOT NULL,
            vendor VARCHAR(200),
            version VARCHAR(200),
            platform VARCHAR(100),
            cpe_uri VARCHAR(500),
            status VARCHAR(30) DEFAULT 'unknown',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_cve ON cve_affected_products (cve_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_cpe ON cve_affected_products (cpe_uri)")
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_products_cve ON cve_affected_products "
        "(cve_id, COALESCE(cpe_uri, ''), COALESCE(vendor, ''), COALESCE(product, ''))"
    )
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cve_patches (
            id SERIAL PRIMARY KEY,
            cve_id VARCHAR(30) REFERENCES cve_entries(cve_id) ON DELETE CASCADE,
            patch_name VARCHAR(300),
            vendor VARCHAR(200),
            url VARCHAR(500),
            version_fixed VARCHAR(200),
            released DATE,
            available BOOLEAN DEFAULT false,
            verified BOOLEAN DEFAULT false,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_patches_cve ON cve_patches (cve_id)")

    # Analyses IA dediees (au lieu de la colonne weaknesses, etrangere et bruitee)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cve_analysis (
            id SERIAL PRIMARY KEY,
            cve_id VARCHAR(30) UNIQUE REFERENCES cve_entries(cve_id) ON DELETE CASCADE,
            summary TEXT,
            impact TEXT,
            recommendation TEXT,
            patched_in VARCHAR(200),
            exploitation_likelihood VARCHAR(20),
            audience VARCHAR(100),
            model VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_cve ON cve_analysis (cve_id)")

    # Historique des decisions (snapshots quotidiens pour suivre l'evolution du risque)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_history (
            id SERIAL PRIMARY KEY,
            cve_id VARCHAR(30) REFERENCES cve_entries(cve_id) ON DELETE CASCADE,
            score INTEGER NOT NULL,
            level VARCHAR(20),
            factors JSONB,
            profile_id INTEGER,
            snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision_hist ON decision_history (profile_id, cve_id, snapshot_at)")

    # Advisories fournisseurs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendor_advisories (
            id SERIAL PRIMARY KEY,
            vendor VARCHAR(200) NOT NULL,
            advisory_id VARCHAR(200),
            title TEXT,
            url VARCHAR(500),
            severity VARCHAR(20),
            published DATE,
            cve_id VARCHAR(30),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_advisories_vendor ON vendor_advisories (vendor)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_advisories_cve ON vendor_advisories (cve_id)")

    # Historique des exports STIX 2.1
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stix_export_logs (
            id SERIAL PRIMARY KEY,
            stix_id VARCHAR(200) UNIQUE NOT NULL,
            stix_type VARCHAR(50),
            object_ref VARCHAR(200),
            export_format VARCHAR(20) DEFAULT 'json',
            raw_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Feedback des decisions (fondation calibration) : comment l'utilisateur
    # a valide/infirme une decision -> ajustement ulterieur des pondérations.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_feedback (
            id SERIAL PRIMARY KEY,
            cve_id VARCHAR(30) NOT NULL,
            decision_score INTEGER,
            action TEXT,                 -- patched | not_relevant | ignored | exploitable | false_positive
            comment TEXT,
            user_ref VARCHAR(100),
            fp_risk_at_decision NUMERIC(6,3),
            applied_patch BOOLEAN,
            was_exploited BOOLEAN,
            source VARCHAR(50) DEFAULT 'api',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_cve ON decision_feedback (cve_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_action ON decision_feedback (action)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_created ON decision_feedback (created_at)")

    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Tables PostgreSQL initialisees.")
