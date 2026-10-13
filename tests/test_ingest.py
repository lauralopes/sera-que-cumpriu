import hashlib
from pypdf import PdfWriter
from backend.db import connect, initialize
from backend.ingest import ingest_document

def test_document_import_is_idempotent_and_does_not_assume_identity(tmp_path):
    db = connect(tmp_path / 'test.sqlite')
    initialize(db)
    p = tmp_path / 'plan.pdf'
    w = PdfWriter(); w.add_blank_page(width=100, height=100)
    with p.open('wb') as f: w.write(f)
    a = ingest_document(db, '2002', p, 'https://example.org/plan.pdf', tmp_path/'copies')
    b = ingest_document(db, '2002', p, 'https://example.org/plan.pdf', tmp_path/'copies')
    assert a == b
    row = dict(db.execute('SELECT * FROM documents WHERE id=?',(a,)).fetchone())
    assert row['sha256'] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert row['pages'] == 1
    assert row['identity_status'] == 'pending'
    assert db.execute('SELECT count(*) FROM pages').fetchone()[0] == 1
    assert (tmp_path/'copies'/row['stored_filename']).exists()
