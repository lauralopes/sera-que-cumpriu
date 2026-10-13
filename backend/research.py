import hashlib
import json
import re
import unicodedata
from datetime import date
from urllib.parse import urlparse
from .ingest import now

STATES = ['Concluída','Parcialmente concluída','Não concluída','Revertida','Evidência insuficiente','Prazo ainda não vencido','Não mensurável','Requer revisão']
DETERMINED = STATES[:4]
CONFIDENCES = ['Alta','Média','Baixa']

def fingerprint(text):
    clean = unicodedata.normalize('NFKD',text.casefold())
    return hashlib.sha256(re.sub(r'\W+',' ',clean).strip().encode()).hexdigest()

def safe_url(url):
    if urlparse(url).scheme not in ('http','https'): raise ValueError('URL deve usar HTTP ou HTTPS')
    return url

def add_commitment(db, record):
    r = dict(record)
    for k in ('id','plan_id','theme','description','nature','criterion','criterion_set_at'):
        if not r.get(k): raise ValueError(f'Campo obrigatório: {k}')
    fp = fingerprint(r['description'])
    prior = db.execute('SELECT id FROM commitments WHERE plan_id=? AND fingerprint=?',(r['plan_id'],fp)).fetchone()
    cid = prior[0] if prior else r['id']
    with db:
        if not prior:
            db.execute('INSERT INTO commitments(id,plan_id,theme,description,nature,measurable,target,unit,deadline,criterion,criterion_set_at,criterion_note,fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (cid,r['plan_id'],r['theme'],r['description'],r['nature'],r.get('measurable',1),r.get('target'),r.get('unit'),r.get('deadline'),r['criterion'],r['criterion_set_at'],r.get('criterion_note',''),fp))
        for ref in r.get('refs',[]):
            text = db.execute('SELECT pg.text,d.plan_id FROM pages pg JOIN documents d ON d.id=pg.document_id WHERE pg.document_id=? AND pg.number=?',(ref['document_id'],ref['page'])).fetchone()
            normalize = lambda s: re.sub(r'\s+',' ',s).strip()
            if not text or text['plan_id']!=r['plan_id'] or normalize(ref['quote']) not in normalize(text[0]):
                raise ValueError('Citação não encontrada na página de origem')
            db.execute('INSERT OR IGNORE INTO promise_refs VALUES(?,?,?,?)',(cid,ref['document_id'],ref['page'],ref['quote']))
    return cid

def add_evidence(db, record):
    r = dict(record); safe_url(r['url'])
    for k in ('title','institution','support','kind'):
        if not r.get(k): raise ValueError(f'Campo obrigatório: {k}')
    for k in ('published_at','covered_start','covered_end','event_date'):
        if r.get(k):date.fromisoformat(r[k])
    if r.get('covered_start') and r.get('covered_end') and r['covered_start']>r['covered_end']:raise ValueError('Período de evidência invertido')
    plan = db.execute('SELECT p.* FROM plans p JOIN commitments c ON c.plan_id=p.id WHERE c.id=?',(r['commitment_id'],)).fetchone()
    if not plan: raise ValueError('Compromisso desconhecido')
    after = bool((r.get('event_date') or r.get('covered_start')) and (r.get('event_date') or r.get('covered_start')) > plan['end'])
    with db:
        db.execute('INSERT OR IGNORE INTO evidence(commitment_id,title,institution,url,published_at,covered_start,covered_end,consulted_at,support,kind,context,event_date,after_exercise,archive_url) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (r['commitment_id'],r['title'],r['institution'],r['url'],r.get('published_at'),r.get('covered_start'),r.get('covered_end'),r.get('consulted_at',now()),r['support'],r['kind'],r.get('context',''),r.get('event_date'),int(after),r.get('archive_url')))
    return db.execute('SELECT id FROM evidence WHERE commitment_id=? AND url=?',(r['commitment_id'],r['url'])).fetchone()[0]

def assess(db, cid, assessment, reason, actor='Codex', human_review=False):
    a=dict(assessment)
    if not reason.strip(): raise ValueError('Justificativa da alteração é obrigatória')
    if a.get('status') not in STATES: raise ValueError('Estado inválido')
    if a.get('confidence') not in CONFIDENCES: raise ValueError('Confiança inválida')
    for k in ('result','justification','confidence_reason','cutoff'):
        if not a.get(k): raise ValueError(f'Campo obrigatório: {k}')
    date.fromisoformat(a['cutoff'])
    c=db.execute('SELECT c.*,p.start,p.end,p.provisional FROM commitments c JOIN plans p ON p.id=c.plan_id WHERE c.id=?',(cid,)).fetchone()
    if not c: raise ValueError('Compromisso desconhecido')
    if not c['measurable'] and a['status']!='Não mensurável': raise ValueError('Item não mensurável excluído do indicador')
    if a['status']=='Prazo ainda não vencido' and not (c['deadline'] and c['deadline']>a['cutoff'] and c['provisional']):
        raise ValueError('Não há prazo explícito futuro em mandato provisório')
    if a['cutoff']>c['end'] or a['cutoff']<c['start']: raise ValueError('Data de corte fora do período avaliado')
    ids=a.get('evidence_ids',[])
    evidence=[]
    for eid in ids:
        e=db.execute('SELECT * FROM evidence WHERE id=? AND commitment_id=?',(eid,cid)).fetchone()
        if not e: raise ValueError('Evidência não pertence ao compromisso')
        evidence.append(e)
    def temporal(e):
        if e['after_exercise']:return False
        if e['event_date']:return c['start']<=e['event_date']<=a['cutoff']
        return bool(e['covered_start'] and e['covered_end'] and c['start']<=e['covered_start']<=e['covered_end']<=a['cutoff'])
    in_period=[e for e in evidence if temporal(e)]
    if a['status'] in DETERMINED and not in_period: raise ValueError('Conclusão determinada exige evidência do período')
    if a['status']=='Não mensurável' and c['measurable']: raise ValueError('Mensurabilidade deve ser revista na extração, não na avaliação')
    prior=db.execute('SELECT id FROM current_assessments WHERE commitment_id=?',(cid,)).fetchone()
    with db:
        cur=db.execute('INSERT INTO assessments(commitment_id,status,result,justification,confidence,confidence_reason,cutoff,human_review,quantitative_progress,calculation,evidence_ids,created_at,actor,change_reason,previous_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (cid,a['status'],a['result'],a['justification'],a['confidence'],a['confidence_reason'],a['cutoff'],int(human_review),a.get('quantitative_progress'),a.get('calculation'),json.dumps(ids),now(),actor,reason,prior[0] if prior else None))
        db.execute('UPDATE assessments SET criterion_snapshot=? WHERE id=?',(c['criterion'],cur.lastrowid))
        db.execute("UPDATE commitments SET research_state='assessed' WHERE id=?",(cid,))
    return cur.lastrowid

def revise_criterion(db,cid,criterion,reason,actor='Codex'):
    if not criterion.strip() or not reason.strip():raise ValueError('Critério e motivo são obrigatórios')
    row=db.execute('SELECT criterion FROM commitments WHERE id=?',(cid,)).fetchone()
    if not row:raise ValueError('Compromisso desconhecido')
    if criterion==row[0]:return
    with db:
        db.execute('INSERT INTO criterion_history(commitment_id,previous_criterion,criterion,reason,actor,created_at) VALUES(?,?,?,?,?,?)',(cid,row[0],criterion,reason,actor,now()))
        db.execute("UPDATE commitments SET criterion=?,criterion_set_at=?,research_state='pending' WHERE id=?",(criterion,now(),cid))

def list_commitments(db):
    rows=[dict(r) for r in db.execute('SELECT c.*,p.president,p.election,p.start,p.end,p.provisional,a.status,a.result,a.justification,a.confidence,a.confidence_reason,a.cutoff,a.human_review,a.quantitative_progress,a.calculation,a.criterion_snapshot,a.id assessment_id FROM commitments c JOIN plans p ON c.plan_id=p.id LEFT JOIN current_assessments a ON a.commitment_id=c.id ORDER BY p.election,c.id')]
    for r in rows:
        r['refs']=[dict(x) for x in db.execute('SELECT r.*,d.source_url,d.title,d.sha256 FROM promise_refs r JOIN documents d ON d.id=r.document_id WHERE r.commitment_id=?',(r['id'],))]
        r['evidence']=[dict(x) for x in db.execute('SELECT * FROM evidence WHERE commitment_id=?',(r['id'],))]
        r['history']=[dict(x) for x in db.execute('SELECT * FROM assessments WHERE commitment_id=? ORDER BY id DESC',(r['id'],))]
        r['criterion_history']=[dict(x) for x in db.execute('SELECT * FROM criterion_history WHERE commitment_id=? ORDER BY id DESC',(r['id'],))]
        if r['assessment_id'] and (r['criterion_snapshot']!=r['criterion'] or r['research_state']!='assessed'):
            r['status']='Requer revisão';r['human_review']=0;r['confidence']='Baixa';r['justification']='Critério alterado após a avaliação; reavaliação obrigatória. Avaliação anterior preservada no histórico.'
    return rows
