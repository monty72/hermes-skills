-- Skills Marketplace Database Schema
-- SQLite with FTS5 for full-text search

-- To init: sqlite3 skills.db < schema.sql
-- To rebuild FTS: INSERT INTO skills_fts(skills_fts) VALUES('rebuild');

CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    author TEXT NOT NULL,
    author_url TEXT,
    description TEXT NOT NULL,
    long_description TEXT,
    category TEXT NOT NULL,
    use_cases TEXT,               -- JSON array
    platforms TEXT,               -- JSON array
    quality_tier TEXT DEFAULT 'promising',  -- excellent, strong, promising
    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    install_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    rating REAL DEFAULT 0.0,
    review_count INTEGER DEFAULT 0,
    github_url TEXT,
    license TEXT,
    language TEXT,
    tags TEXT,                     -- JSON array
    security_score INTEGER,
    security_verified BOOLEAN DEFAULT 0,
    last_security_scan TEXT,
    is_verified BOOLEAN DEFAULT 0,
    is_premium BOOLEAN DEFAULT 0,
    premium_price REAL DEFAULT 0.0,
    version TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_indexed TEXT
);

CREATE TABLE IF NOT EXISTS skill_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id TEXT NOT NULL REFERENCES skills(id),
    filename TEXT NOT NULL,
    content TEXT NOT NULL,
    file_type TEXT DEFAULT 'other',
    UNIQUE(skill_id, filename)
);

CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    slug TEXT NOT NULL UNIQUE,
    skill_ids TEXT NOT NULL,
    is_premium BOOLEAN DEFAULT 0,
    premium_price REAL DEFAULT 0.0,
    discount_label TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS authors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    github_url TEXT,
    website_url TEXT,
    bio TEXT,
    avatar_url TEXT,
    skill_count INTEGER DEFAULT 0,
    total_stars INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id TEXT NOT NULL REFERENCES skills(id),
    author_name TEXT,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    review_text TEXT,
    verified_purchase BOOLEAN DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id TEXT REFERENCES skills(id),
    action_type TEXT NOT NULL,
    agent_type TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skill_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id TEXT NOT NULL REFERENCES skills(id),
    version TEXT NOT NULL,
    changelog TEXT,
    files_hash TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS security_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id TEXT NOT NULL REFERENCES skills(id),
    scanner_type TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    results_json TEXT,
    scanned_at TEXT NOT NULL
);

-- FTS5 for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts USING fts5(
    name, description, tags, author,
    content='skills', content_rowid='rowid'
);

CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category);
CREATE INDEX IF NOT EXISTS idx_skills_author ON skills(author);
CREATE INDEX IF NOT EXISTS idx_skills_quality ON skills(quality_tier);
CREATE INDEX IF NOT EXISTS idx_skills_stars ON skills(stars DESC);
CREATE INDEX IF NOT EXISTS idx_skills_updated ON skills(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_skills_created ON skills(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_skill ON activity_log(skill_id);
CREATE INDEX IF NOT EXISTS idx_activity_time ON activity_log(created_at DESC);
