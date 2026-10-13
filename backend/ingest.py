import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from pypdf import PdfReader
from .db import ROOT, DATA, connect, initialize

def now():
    return datetime.now(timezone.utc).isoformat()

def seed_plans(db):
    for p in json.loads((ROOT/'sources/plans.json').read_text()):
        db.execute('INSERT OR IGNORE INTO plans(id,president,election,start,end,provisional,period_sources) VALUES(?,?,?,?,?,?,?)',
                   (p['id'],p['president'],p['election'],p['start'],p['end'],p['provisional'],json.dumps(p['period_sources'])))
    db.commit()

def ingest_document(db, plan_id, path, url, storage=None):
    seed_plans(db)
    path = Path(path)
    raw = path.read_bytes()
    if not raw.startswith(b'%PDF'): raise ValueError('O arquivo não é um PDF')
    digest = hashlib.sha256(raw).hexdigest()
    previous = db.execute('SELECT id FROM documents WHERE plan_id=? AND sha256=?',(plan_id,digest)).fetchone()
    if previous: return previous[0]
    reader = PdfReader(path)
    if reader.is_encrypted: raise ValueError('PDF criptografado requer revisão')
    storage = Path(storage or DATA/'documents'); storage.mkdir(parents=True, exist_ok=True)
    stored = f'{plan_id}-{digest[:16]}.pdf'
    shutil.copy2(path, storage/stored)
    with db:
        cur = db.execute('INSERT INTO documents(plan_id,sha256,filename,stored_filename,source_url,consulted_at,bytes,pages,metadata) VALUES(?,?,?,?,?,?,?,?,?)',
            (plan_id,digest,path.name,stored,url,now(),len(raw),len(reader.pages),json.dumps({str(k):str(v) for k,v in (reader.metadata or {}).items()},ensure_ascii=False)))
        doc_id = cur.lastrowid
        for i,page in enumerate(reader.pages):
            db.execute('INSERT INTO pages(document_id,number,text) VALUES(?,?,?)',(doc_id,i+1,page.extract_text() or ''))
    return doc_id

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('folder',type=Path)
    args = parser.parse_args(); db=connect(); initialize(db); seed_plans(db)
    for p in json.loads((ROOT/'sources/plans.json').read_text()):
        matches = [f for f in args.folder.glob('*.pdf') if p['id'] in f.name]
        if not matches: print(p['id'],'pendente: PDF ausente'); continue
        for f in matches: print(p['id'],ingest_document(db,p['id'],f,p['url']))
