CREATE TABLE IF NOT EXISTS plans (
 id TEXT PRIMARY KEY, president TEXT NOT NULL, election INTEGER NOT NULL,
 start TEXT NOT NULL, end TEXT NOT NULL, provisional INTEGER NOT NULL DEFAULT 0,
 extraction_complete INTEGER NOT NULL DEFAULT 0, period_sources TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS documents (
 id INTEGER PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES plans(id), sha256 TEXT NOT NULL,
 filename TEXT NOT NULL, stored_filename TEXT NOT NULL, source_url TEXT NOT NULL,
 consulted_at TEXT NOT NULL, bytes INTEGER NOT NULL, pages INTEGER NOT NULL, metadata TEXT NOT NULL,
 identity_status TEXT NOT NULL DEFAULT 'pending', title TEXT, version TEXT, document_date TEXT,
 identity_note TEXT, UNIQUE(plan_id, sha256)
);
CREATE TABLE IF NOT EXISTS pages (
 document_id INTEGER NOT NULL REFERENCES documents(id), number INTEGER NOT NULL,
 printed_number TEXT, text TEXT NOT NULL, extraction_reviewed INTEGER NOT NULL DEFAULT 0,
 review_note TEXT, PRIMARY KEY(document_id, number)
);
CREATE TABLE IF NOT EXISTS commitments (
 id TEXT PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES plans(id), theme TEXT NOT NULL,
 description TEXT NOT NULL, nature TEXT NOT NULL, measurable INTEGER NOT NULL DEFAULT 1,
 target REAL, unit TEXT, deadline TEXT, criterion TEXT NOT NULL, criterion_set_at TEXT NOT NULL,
 criterion_note TEXT NOT NULL DEFAULT '', fingerprint TEXT NOT NULL,
 research_state TEXT NOT NULL DEFAULT 'pending', UNIQUE(plan_id, fingerprint)
);
CREATE TABLE IF NOT EXISTS promise_refs (
 commitment_id TEXT NOT NULL REFERENCES commitments(id), document_id INTEGER NOT NULL REFERENCES documents(id),
 page INTEGER NOT NULL, quote TEXT NOT NULL, PRIMARY KEY(commitment_id, document_id, page, quote),
 FOREIGN KEY(document_id,page) REFERENCES pages(document_id,number)
);
CREATE TABLE IF NOT EXISTS evidence (
 id INTEGER PRIMARY KEY, commitment_id TEXT NOT NULL REFERENCES commitments(id), title TEXT NOT NULL,
 institution TEXT NOT NULL, url TEXT NOT NULL, published_at TEXT, covered_start TEXT, covered_end TEXT,
 consulted_at TEXT NOT NULL, support TEXT NOT NULL, kind TEXT NOT NULL, context TEXT NOT NULL DEFAULT '',
 event_date TEXT, after_exercise INTEGER NOT NULL DEFAULT 0, archive_url TEXT, UNIQUE(commitment_id,url)
);
CREATE TABLE IF NOT EXISTS criterion_history (
 id INTEGER PRIMARY KEY, commitment_id TEXT NOT NULL REFERENCES commitments(id),
 previous_criterion TEXT NOT NULL, criterion TEXT NOT NULL, reason TEXT NOT NULL,
 actor TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assessments (
 id INTEGER PRIMARY KEY, commitment_id TEXT NOT NULL REFERENCES commitments(id), status TEXT NOT NULL,
 result TEXT NOT NULL, justification TEXT NOT NULL, confidence TEXT NOT NULL, confidence_reason TEXT NOT NULL,
 cutoff TEXT NOT NULL, human_review INTEGER NOT NULL DEFAULT 0, quantitative_progress REAL,
 calculation TEXT, evidence_ids TEXT NOT NULL, created_at TEXT NOT NULL,
 actor TEXT NOT NULL, change_reason TEXT NOT NULL, previous_id INTEGER REFERENCES assessments(id)
);
CREATE TABLE IF NOT EXISTS tasks (
 id INTEGER PRIMARY KEY, kind TEXT NOT NULL, task_key TEXT NOT NULL UNIQUE, payload TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0, lease_until REAL,
 worker_id TEXT, available_at REAL NOT NULL DEFAULT 0, result TEXT, error TEXT,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS controls (key TEXT PRIMARY KEY, value TEXT NOT NULL);
INSERT OR IGNORE INTO controls VALUES('paused','0');
CREATE TABLE IF NOT EXISTS archive_cache (
 url TEXT NOT NULL, requested_timestamp TEXT NOT NULL, response TEXT NOT NULL, consulted_at TEXT NOT NULL,
 PRIMARY KEY(url, requested_timestamp)
);
CREATE TABLE IF NOT EXISTS domain_access (domain TEXT PRIMARY KEY, last_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, task_id INTEGER, message TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE VIEW IF NOT EXISTS current_assessments AS
 SELECT a.* FROM assessments a WHERE a.id=(SELECT max(b.id) FROM assessments b WHERE b.commitment_id=a.commitment_id);
