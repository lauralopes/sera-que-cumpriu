import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get('AUDIT_DATA_DIR', ROOT / 'data'))

def connect(path=None):
    target = Path(path) if path else DATA / 'audit.sqlite'
    target.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(target, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    return db

def initialize(db):
    db.executescript((ROOT/'backend/schema.sql').read_text())
    if 'criterion_snapshot' not in {r[1] for r in db.execute('PRAGMA table_info(assessments)')}:
        db.execute('ALTER TABLE assessments ADD COLUMN criterion_snapshot TEXT')
        db.execute('UPDATE assessments SET criterion_snapshot=(SELECT criterion FROM commitments WHERE id=commitment_id)')
    db.commit()
