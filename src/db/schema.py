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

    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Tables PostgreSQL initialisees.")
