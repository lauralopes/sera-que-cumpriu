"""Reproduce the initial research from user-supplied PDFs. Never fabricates missing sources."""
import argparse,json,re
from pathlib import Path
from .db import ROOT,DATA,connect,initialize
from .ingest import ingest_document,seed_plans
from .research import add_commitment,add_evidence,assess
from .queue import enqueue

# Selectors are short retrieval anchors; literal excerpts are obtained only from local PDFs.
CATALOG=[
 ('2002',44,'Cartão de alimentação para famílias muito pobres','Renda','ação',r'Para atacar de imediato',None,None),
 ('2002',31,'Reajustar progressivamente o poder de compra do salário mínimo','Trabalho','resultado',r'Além disso, visando aumentar',None,None),
 ('2002',57,'Propor Conselho Nacional de Políticas Regionais','Desenvolvimento regional','ação',r'O novo governo proporá',None,None),
 ('2010',7,'Criar seis mil creches e pré-escolas','Educação','entrega',r'O Governo Federal assumi',6000,'unidades'),
 ('2010',7,'Criar dez mil quadras esportivas cobertas','Educação','entrega',r'O Governo Federal assumi',10000,'quadras'),
 ('2010',7,'Garantir escola técnica em cidades polo ou com mais de 50 mil habitantes','Educação','entrega',r'As cidades',None,None),
 ('2010',8,'Implantar o Vale Cultura','Cultura','ação',r'Será implantado o',None,None),
 ('2010',8,'Construir mais dois milhões de moradias pelo Minha Casa Minha Vida','Habitação','entrega',r'T erá particular relevância',2000000,'moradias'),
 ('2010',8,'Ofertar gratuitamente remédios contra hipertensão e diabetes','Saúde','entrega',r'A universalização da saúde dar',None,None),
 ('2010',8,'Criar programa nacional de defesa urbana para prevenir desastres ambientais','Meio ambiente','ação',r'Um programa nacional de defesa urbana',None,None),
 ('2010',7,'Erradicar o analfabetismo por mobilização nacional','Educação','resultado',r'Uma am',None,None),
 ('2014',33,'Criar Academia Nacional de Segurança Pública','Segurança','ação',r'está prevista também a criação',None,None),
 ('2014',30,'Universalizar educação infantil para crianças de 4 a 5 anos até 2016','Educação','resultado',r'vamos continuar ampliando o atendimento',None,None),
 ('2014',30,'Alcançar educação em tempo integral em 20% da rede pública até 2018','Educação','resultado',r'vamos continuar ampliando e qualificando',20,'% da rede'),
 ('2014',30,'Conceder mais cem mil bolsas Ciência sem Fronteiras entre 2015 e 2018','Ciência e tecnologia','entrega',r'vamos conceder',100000,'bolsas'),
 ('2014',36,'Realizar 137 mil ligações do Luz para Todos em localidades isoladas entre 2015 e 2018','Energia','entrega',r'Será também dedicado todo empenho',137000,'ligações'),
 ('2014',35,'Universalizar acesso a internet barata rápida e segura','Comunicações','resultado',r'vamos promover a',None,None),
 ('2018',59,'Estabelecer independência formal do Banco Central com mandatos fixos','Economia','ação',r'No entanto, avançamos institucionalmente',None,None),
 ('2018',53,'Reunir Fazenda Planejamento e Indústria e Comércio no Ministério da Economia','Gestão pública','ação',r'Para atender ao objetivo',None,None),
 ('2018',59,'Manter inflação baixa e previsível','Economia','manutenção',r'Inflação baixa e previsível',None,None),
 ('2022',5,'Implantar Bolsa Família renovado e ampliado','Renda','ação',r'Um programa Bolsa Família renovado',None,None),
 ('2010',5,'Expandir e fortalecer a democracia política econômica e social','Democracia','orientação genérica',r'Expandir e fortalecer a democracia',None,None),
 ('2022',4,'Propor nova legislação trabalhista com proteção às formas de ocupação','Trabalho','ação',r'O novo governo irá propor',None,None)
]
CRITERIA={
 'Cartão de alimentação para famílias muito pobres':'Comprovar cartão e benefício de alimentação operacionais a famílias muito pobres no mandato 2003–2006; instituição legal sem pagamento não basta. Sem meta universal explícita neste trecho.',
 'Implantar o Vale Cultura':'Comprovar instituição, regulamentação e distribuição/uso efetivo por trabalhadores entre 2011 e 2014. O trecho não promete adesão universal.',
 'Estabelecer independência formal do Banco Central com mandatos fixos':'Comprovar norma de autonomia formal vigente e regime de mandatos fixos implementado no mandato 2019–2022. Inflação é compromisso separado.',
 'Criar seis mil creches e pré-escolas':'Comprovar 6.000 novas unidades concluídas e disponíveis até 31/12/2014; contratação, financiamento e início de obra não são entrega.',
 'Criar dez mil quadras esportivas cobertas':'Comprovar 10.000 novas quadras cobertas concluídas e disponíveis até 31/12/2014, separando reforma de construção e obras contratadas de entregas.',
 'Construir mais dois milhões de moradias pelo Minha Casa Minha Vida':'Comprovar mais de 2.000.000 moradias construídas e entregues entre 2011 e 2014; separar contratações e unidades concluídas antes do mandato.',
 'Criar Academia Nacional de Segurança Pública':'Comprovar criação e atividade efetiva da academia durante o exercício 2015–11/05/2016; entregas no dia 12/05 exigem conferência de horário e as posteriores ficam separadas.',
}

CRITERIA.update(json.loads((ROOT/'sources/criteria.json').read_text()))

def excerpt(text,pattern):
    text=re.sub(r'\s+',' ',text).strip();m=re.search(pattern,text,re.I)
    if not m:raise ValueError('Âncora não encontrada: '+pattern)
    start=m.start();ends=[text.find(c,m.end()) for c in '.;'];end=min((x for x in ends if x>=0),default=-1)
    return text[start:end+1 if end>=0 else len(text)]

def bootstrap(folder):
    db=connect();initialize(db);seed_plans(db)
    plans=json.loads((ROOT/'sources/plans.json').read_text())
    for p in plans:
        with db:db.execute('UPDATE plans SET period_sources=? WHERE id=?',(json.dumps(p['period_sources']),p['id']))
        matches=[f for f in Path(folder).glob('*.pdf') if p['id'] in f.name]
        if matches:
            did=ingest_document(db,p['id'],matches[0],p['url'])
            titles={'2002':'Programa de Governo 2002','2006':'Lula Presidente — Programa de Governo 2007/2010','2010':'Os 13 compromissos programáticos de Dilma Rousseff para debate na sociedade brasileira','2014':'Mais Mudanças, Mais Futuro — Programa de Governo Dilma Rousseff 2014','2018':'O Caminho da Prosperidade — Proposta de Plano de Governo','2022':'Diretrizes para o Programa de Reconstrução e Transformação do Brasil — Lula Alckmin 2023–2026'}
            with db:db.execute('UPDATE documents SET title=?,version=?,document_date=?,identity_status=?,identity_note=? WHERE id=?',
                (titles[p['id']],'Cópia fornecida pelo usuário; título conferido na capa','setembro–outubro de 2010' if p['id']=='2010' else None,'identified_copy','PDF legível e hash preservado. Identidade pelo conteúdo da capa; autenticidade, data exata e equivalência com registro eleitoral original pendentes. Sem confirmação criptográfica de autoria.',did))
        else:enqueue(db,'download_plan','plan:'+p['id'],{'plan_id':p['id'],'url':p['url']})
    counts={}
    for plan,page,description,theme,nature,pattern,target,unit in CATALOG:
        d=db.execute('SELECT id FROM documents WHERE plan_id=? ORDER BY id LIMIT 1',(plan,)).fetchone()
        if not d:continue
        pg=db.execute('SELECT text FROM pages WHERE document_id=? AND number=?',(d[0],page)).fetchone()
        try:quote=excerpt(pg[0],pattern)
        except ValueError as e:print(description,str(e));continue
        counts[plan]=counts.get(plan,0)+1;cid=f'{plan}-{counts[plan]:03d}'
        measurable=nature!='orientação genérica'
        criterion=CRITERIA.get(description)
        if not measurable:criterion='Orientação genérica de fortalecimento democrático sem meta, universo ou critério objetivo explícito; fora dos percentuais de cumprimento.'
        if not criterion:
            criterion=f'Conferir execução integral do compromisso “{description}” no período de exercício, com documentação primária, linha de base e universo aplicáveis. Critério operacional detalhado pendente; não classificar antes de refiná-lo.'
        deadline='2016-12-31' if 'até 2016' in description else '2018-12-31' if '2018' in description else None
        cid=add_commitment(db,dict(id=cid,plan_id=plan,theme=theme,description=description,nature=nature,measurable=int(measurable),target=target,unit=unit,deadline=deadline,criterion=criterion,criterion_set_at='2026-10-13',criterion_note='Extração piloto parcial; critérios formulados após reconhecimento inicial de fontes, antes de qualquer classificação. Critérios genéricos ainda exigem refinamento.',refs=[dict(document_id=d[0],page=page,quote=quote)]))
        if not measurable and not db.execute('SELECT 1 FROM current_assessments WHERE commitment_id=?',(cid,)).fetchone():
            assess(db,cid,dict(status='Não mensurável',result='Orientação genérica preservada',justification='Sem parâmetro objetivo suficiente no texto; não inventar limiar de fortalecimento democrático.',confidence='Média',confidence_reason='Classificação da natureza do trecho, pendente de revisão humana; não é julgamento da democracia no período.',cutoff=db.execute('SELECT end FROM plans WHERE id=?',(plan,)).fetchone()[0],evidence_ids=[]),'Classificação inicial da natureza da promessa')
        if not db.execute('SELECT 1 FROM current_assessments WHERE commitment_id=?',(cid,)).fetchone():enqueue(db,'research_commitment','commitment:'+cid,{'commitment_id':cid})
    # Save page-review tasks independently of promise research. No page automatically becomes reviewed.
    for pg in db.execute('SELECT document_id,number FROM pages ORDER BY document_id,number'):
        enqueue(db,'review_page',f'page:{pg[0]}:{pg[1]}',{'document_id':pg[0],'page':pg[1]})
    # Initial sourced findings are our own summaries; no full articles distributed.
    findings=json.loads((ROOT/'research/initial-findings.json').read_text())
    for f in findings:
        c=db.execute('SELECT id FROM commitments WHERE description=? AND plan_id=?',(f['description'],f['plan_id'])).fetchone()
        if not c:continue
        ids=[]
        for ev in f['evidence']:ids.append(add_evidence(db,dict(commitment_id=c[0],consulted_at='2026-10-13',**ev)))
        if not db.execute('SELECT 1 FROM current_assessments WHERE commitment_id=?',(c[0],)).fetchone():
            assess(db,c[0],dict(evidence_ids=ids,**f['assessment']),'Avaliação piloto com fontes consultadas nesta sessão')
        with db:db.execute("UPDATE tasks SET state='done',result=? WHERE task_key=? AND state IN ('queued','needs_review')",(json.dumps({'note':'Avaliação inicial salva; sem revisão humana'}),'commitment:'+c[0]))
    manifest=[dict(r) for r in db.execute('SELECT * FROM documents')]
    DATA.mkdir(exist_ok=True);(DATA/'document-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print('Compromissos',db.execute('SELECT count(*) FROM commitments').fetchone()[0],'avaliações',db.execute('SELECT count(*) FROM current_assessments').fetchone()[0])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);args=p.parse_args();bootstrap(args.folder)
