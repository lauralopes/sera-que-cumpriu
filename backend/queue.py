import json
import time
from .ingest import now

def enqueue(db, kind, key, payload):
    with db:
        db.execute('INSERT OR IGNORE INTO tasks(kind,task_key,payload,created_at,updated_at) VALUES(?,?,?,?,?)',(kind,key,json.dumps(payload),now(),now()))
    return db.execute('SELECT id FROM tasks WHERE task_key=?',(key,)).fetchone()[0]

def control(db, action, task_id=None):
    if action not in ('pause','resume','cancel','retry'): raise ValueError('Ação inválida')
    with db:
        if action in ('pause','resume'):
            db.execute("UPDATE controls SET value=? WHERE key='paused'",('1' if action=='pause' else '0',))
        else:
            if task_id is None: raise ValueError('Informe a tarefa')
            if action=='cancel': db.execute("UPDATE tasks SET state='cancelled',lease_until=NULL,updated_at=? WHERE id=? AND state NOT IN ('done','cancelled')",(now(),task_id))
            else: db.execute("UPDATE tasks SET state='queued',attempts=0,available_at=0,lease_until=NULL,error=NULL,updated_at=? WHERE id=? AND state IN ('error','cancelled')",(now(),task_id))

def claim(db, worker_id, lease_seconds=120):
    t=time.time()
    db.execute('BEGIN IMMEDIATE')
    try:
        if db.execute("SELECT value FROM controls WHERE key='paused'").fetchone()[0]=='1': db.commit();return None
        db.execute("UPDATE tasks SET state='queued',worker_id=NULL,lease_until=NULL WHERE state='running' AND lease_until<?",(t,))
        row=db.execute("SELECT * FROM tasks WHERE state='queued' AND available_at<=? ORDER BY id LIMIT 1",(t,)).fetchone()
        if not row: db.commit();return None
        db.execute("UPDATE tasks SET state='running',worker_id=?,lease_until=?,attempts=attempts+1,updated_at=? WHERE id=?",(worker_id,t+lease_seconds,now(),row['id']))
        result=dict(db.execute('SELECT * FROM tasks WHERE id=?',(row['id'],)).fetchone()); db.commit();return result
    except Exception: db.rollback();raise

def finish(db, tid, worker_id, result=None, error=None, needs_review=False):
    task=db.execute('SELECT * FROM tasks WHERE id=?',(tid,)).fetchone()
    if not task or task['state']!='running' or task['worker_id']!=worker_id:return False
    state='needs_review' if needs_review else 'done'
    if error: state='queued' if task['attempts']<3 else 'error'
    with db:
        db.execute('UPDATE tasks SET state=?,result=?,error=?,available_at=?,lease_until=NULL,updated_at=? WHERE id=? AND state=? AND worker_id=?',
            (state,json.dumps(result,ensure_ascii=False) if result is not None else None,str(error) if error else None,time.time()+min(300,10*2**task['attempts']) if error else 0,now(),tid,'running',worker_id))
        db.execute('INSERT INTO events(task_id,message,created_at) VALUES(?,?,?)',(tid,str(error) if error else state,now()))
    return True

def reserve_domain(db, domain, seconds=3):
    db.execute('BEGIN IMMEDIATE')
    try:
        t=time.time();row=db.execute('SELECT last_at FROM domain_access WHERE domain=?',(domain,)).fetchone()
        slot=max(t,row[0]+seconds if row else t)
        db.execute('INSERT INTO domain_access VALUES(?,?) ON CONFLICT(domain) DO UPDATE SET last_at=excluded.last_at',(domain,slot))
        db.commit();return max(0,slot-t)
    except Exception:db.rollback();raise
