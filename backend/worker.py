import argparse
import json
import re
import time
import uuid
from urllib.parse import urlparse
from .transport import get_bytes
from .db import connect, initialize, DATA
from .queue import claim,finish,reserve_domain
from .archive import wayback,validate_public_url
from .ingest import ingest_document

def execute(db,task):
    p=json.loads(task['payload']);kind=task['kind']
    if kind=='review_page':
        row=db.execute('SELECT text FROM pages WHERE document_id=? AND number=?',(p['document_id'],p['page'])).fetchone()
        if not row:raise ValueError('Página ausente')
        # Candidates are leads, never commitments or conclusions.
        sentences=re.split(r'(?<=[.;])\s+|\n\s*§',re.sub(r'\s+',' ',row['text']))
        candidates=[s for s in sentences if re.search(r'\b(será|serão|vamos|criar|ampliar|implantar|garantir|manter|promover|nosso governo|nosso programa)\b',s,re.I)]
        return {'page':p['page'],'candidates':candidates,'note':'Triagem automática; ler a página integral antes de extrair. Pode omitir ou incluir trechos indevidos.'},True
    if kind=='research_commitment':
        return {'commitment_id':p['commitment_id'],'note':'Pesquisa substantiva e julgamento pendentes. Consultar docs/RETOMAR.md; nenhuma classificação automática.'},True
    if kind=='wayback':
        time.sleep(reserve_domain(db,'archive.org'));return wayback(db,p['url'],p.get('timestamp','')),False
    if kind=='download_plan':
        url=validate_public_url(p['url'],resolve=True);time.sleep(reserve_domain(db,urlparse(url).hostname))
        content=get_bytes(url,timeout=25)
        if not content.startswith(b'%PDF'):raise ValueError('Fonte devolveu HTML ou outro formato; PDF não importado')
        if len(content)>30_000_000:raise ValueError('PDF excede limite')
        folder=DATA/'downloads';folder.mkdir(parents=True,exist_ok=True);path=folder/f'{task["id"]}.pdf';path.write_bytes(content)
        return {'document_id':ingest_document(db,p['plan_id'],path,url)},False
    raise ValueError('Tipo de tarefa desconhecido')

def run_worker(once=False,worker_id=None):
    db=connect();initialize(db);worker_id=worker_id or uuid.uuid4().hex
    while True:
        task=claim(db,worker_id)
        if task:
            try:
                result,review=execute(db,task);finish(db,task['id'],worker_id,result,needs_review=review)
            except Exception as e:finish(db,task['id'],worker_id,error=f'{type(e).__name__}: {e}')
        if once:break
        time.sleep(.5 if task else 2)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args();run_worker(args.once)
