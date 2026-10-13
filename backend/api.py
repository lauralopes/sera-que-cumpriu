import json
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import Response,FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from .db import connect,initialize,ROOT,DATA
from .ingest import seed_plans
from .research import list_commitments,assess,add_evidence,revise_criterion,add_commitment
from .metrics import summaries
from .queue import control,enqueue
from .archive import validate_public_url
from .export import export_bytes

class ControlBody(BaseModel):
    action: Literal['pause','resume','cancel','retry']
    task_id:int|None=None

class ArchiveBody(BaseModel):
    url:str=Field(max_length=2048)
    timestamp:str=Field(default='',pattern=r'^\d{0,14}$')

class RevisionBody(BaseModel):
    status:str
    result:str=Field(min_length=1,max_length=10000)
    justification:str=Field(min_length=1,max_length=10000)
    confidence:str
    confidence_reason:str=Field(min_length=1,max_length=5000)
    cutoff:str=Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    evidence_ids:list[int]=Field(default_factory=list,max_length=100)
    reason:str=Field(min_length=1,max_length=5000)
    actor:str=Field(default='Usuário local',min_length=1,max_length=100)
    human_review:bool=False

class EvidenceBody(BaseModel):
    title:str=Field(min_length=1,max_length=1000)
    institution:str=Field(min_length=1,max_length=300)
    url:str=Field(max_length=2048)
    published_at:str|None=None
    covered_start:str|None=None
    covered_end:str|None=None
    support:str=Field(min_length=1,max_length=10000)
    kind:Literal['primary','audit','academic','news','opinion','archive']
    context:str=Field(default='',max_length=5000)
    event_date:str|None=None

class CriterionBody(BaseModel):
    criterion:str=Field(min_length=1,max_length=10000)
    reason:str=Field(min_length=1,max_length=5000)
    actor:str=Field(default='Usuário local',min_length=1,max_length=100)

class ExtractionBody(BaseModel):
    id:str=Field(min_length=1,max_length=100,pattern=r'^[A-Za-z0-9_-]+$')
    plan_id:str
    theme:str=Field(min_length=1,max_length=100)
    description:str=Field(min_length=1,max_length=1000)
    nature:Literal['ação','entrega','resultado','manutenção','orientação genérica']
    measurable:bool=True
    criterion:str=Field(min_length=1,max_length=10000)
    document_id:int
    page:int
    quote:str=Field(min_length=1,max_length=10000)

class PageReviewBody(BaseModel):
    reason:str=Field(min_length=1,max_length=5000)

def create_app(db_path=None):
    app=FastAPI(title='O governo cumpriu o plano?',docs_url=None,redoc_url=None)
    db=connect(db_path);initialize(db);seed_plans(db);db.close()

    @app.middleware('http')
    async def protect(request:Request,call_next):
        if request.url.hostname not in ('127.0.0.1','localhost','::1'):
            return Response('Host local obrigatório',status_code=400)
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin=request.headers.get('origin')
            if request.headers.get('x-audit-client')!='local-browser' or (origin and urlparse(origin).netloc!=request.headers.get('host')):
                return Response('Requisição local da aplicação exigida',status_code=403)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        return response

    def read(fn):
        db=connect(db_path)
        try:return fn(db)
        finally:db.close()

    @app.get('/api/plans')
    def plans():return read(lambda d:[dict(p) for p in d.execute('SELECT * FROM plans ORDER BY election')])

    @app.get('/api/documents')
    def documents():return read(lambda d:[dict(p) for p in d.execute('SELECT * FROM documents ORDER BY plan_id')])

    @app.get('/api/documents/{doc_id}/pages/{page}')
    def page(doc_id:int,page:int):
        row=read(lambda d:d.execute('SELECT * FROM pages WHERE document_id=? AND number=?',(doc_id,page)).fetchone())
        if not row:raise HTTPException(404,'Página ausente')
        return dict(row)

    @app.get('/api/documents/{doc_id}/pdf')
    def pdf(doc_id:int):
        row=read(lambda d:d.execute('SELECT stored_filename FROM documents WHERE id=?',(doc_id,)).fetchone())
        if not row:raise HTTPException(404,'Documento ausente')
        return FileResponse(DATA/'documents'/row[0],media_type='application/pdf')

    def filtered(plan=None,q='',theme=None,status=None,confidence=None):
        rows=read(list_commitments)
        return [r for r in rows if (not plan or r['plan_id']==plan) and (not theme or r['theme']==theme) and
                (not status or (r['status'] or 'Pendente')==status) and (not confidence or r['confidence']==confidence) and
                (not q or q.casefold() in json.dumps(r,ensure_ascii=False).casefold())]

    @app.get('/api/commitments')
    def commitments(plan:str|None=None,q:str='',theme:str|None=None,status:str|None=None,confidence:str|None=None):return filtered(plan,q,theme,status,confidence)

    @app.get('/api/summary')
    def summary():return read(summaries)

    @app.get('/api/progress')
    def progress():
        def snapshot(d):
            return dict(paused=d.execute("SELECT value FROM controls WHERE key='paused'").fetchone()[0]=='1',
                counts={r['state']:r['n'] for r in d.execute('SELECT state,count(*) n FROM tasks GROUP BY state')},
                tasks=[dict(r) for r in d.execute('SELECT * FROM tasks ORDER BY id')],
                events=[dict(r) for r in d.execute('SELECT * FROM events ORDER BY id DESC LIMIT 20')],
                archives=[dict(r) for r in d.execute('SELECT * FROM archive_cache ORDER BY consulted_at DESC')])
        return read(snapshot)

    @app.post('/api/queue/control')
    def queue_control(body:ControlBody):
        try:read(lambda d:control(d,body.action,body.task_id));return {'ok':True}
        except ValueError as e:raise HTTPException(422,str(e))

    @app.post('/api/archive')
    def archive(body:ArchiveBody):
        try:
            validate_public_url(body.url)
            tid=read(lambda d:enqueue(d,'wayback','wayback:'+body.url+':'+body.timestamp,body.model_dump()))
            return {'task_id':tid}
        except ValueError as e:raise HTTPException(422,str(e))

    @app.post('/api/commitments/{cid}/evidence')
    def evidence(cid:str,body:EvidenceBody):
        try:return {'id':read(lambda d:add_evidence(d,dict(commitment_id=cid,**body.model_dump())))}
        except ValueError as e:raise HTTPException(422,str(e))

    @app.post('/api/commitments/{cid}/criterion')
    def criterion(cid:str,body:CriterionBody):
        try:read(lambda d:revise_criterion(d,cid,body.criterion,body.reason,body.actor));return {'ok':True}
        except ValueError as e:raise HTTPException(422,str(e))

    @app.post('/api/commitments')
    def extract(body:ExtractionBody):
        from .ingest import now
        try:
            r=body.model_dump();r['criterion_set_at']=now();r['refs']=[dict(document_id=r.pop('document_id'),page=r.pop('page'),quote=r.pop('quote'))]
            cid=read(lambda d:add_commitment(d,r));read(lambda d:enqueue(d,'research_commitment','commitment:'+cid,{'commitment_id':cid}));return {'id':cid}
        except (ValueError,KeyError) as e:raise HTTPException(422,str(e))

    @app.post('/api/documents/{doc_id}/pages/{page}/review')
    def reviewed(doc_id:int,page:int,body:PageReviewBody):
        def mark(d):
            with d:
                cur=d.execute('UPDATE pages SET extraction_reviewed=1,review_note=? WHERE document_id=? AND number=?',(body.reason,doc_id,page))
                if not cur.rowcount:raise ValueError('Página ausente')
                d.execute("UPDATE tasks SET state='done' WHERE task_key=?",(f'page:{doc_id}:{page}',))
        try:read(mark);return {'ok':True}
        except ValueError as e:raise HTTPException(422,str(e))

    @app.post('/api/commitments/{cid}/revisions')
    def revision(cid:str,body:RevisionBody):
        try:return {'id':read(lambda d:assess(d,cid,body.model_dump(),body.reason,body.actor,body.human_review))}
        except ValueError as e:raise HTTPException(422,str(e))

    @app.get('/api/export')
    def export(format:Literal['csv','xlsx']='xlsx',plan:str|None=None,q:str='',theme:str|None=None,status:str|None=None,confidence:str|None=None):
        raw=export_bytes(filtered(plan,q,theme,status,confidence),format,read(summaries))
        return Response(raw,media_type='text/csv; charset=utf-8' if format=='csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':f'attachment; filename="compromissos.{format}"'})

    dist=ROOT/'frontend/dist'
    if dist.exists():app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
    return app

app=create_app()
