import pytest
from backend.db import connect,initialize
from backend.ingest import seed_plans
from backend.research import add_commitment,add_evidence,assess

def record(plan='2014'):
    return dict(id='C1',plan_id=plan,theme='Segurança',description='Criar uma academia',nature='ação',measurable=1,criterion='Academia operante no exercício',criterion_set_at='2026-10-13',refs=[])

def test_duplicate_and_revision_and_out_of_period_evidence(tmp_path):
    db=connect(tmp_path/'a.sqlite');initialize(db);seed_plans(db)
    assert add_commitment(db,record())=='C1'
    r=record();r['id']='C2'; assert add_commitment(db,r)=='C1'
    a=dict(status='Concluída',result='Academia aberta',justification='Operação',confidence='Alta',confidence_reason='Registro de execução',cutoff='2016-05-11',evidence_ids=[])
    with pytest.raises(ValueError): assess(db,'C1',a,'teste')
    eid=add_evidence(db,dict(commitment_id='C1',title='Registro',institution='Instituição',url='https://example.org',support='Academia aberta em 2017',kind='primary',event_date='2017-01-01',covered_start='2017-01-01',covered_end='2017-01-01'))
    a['evidence_ids']=[eid]
    with pytest.raises(ValueError): assess(db,'C1',a,'fora de período')
    a['status']='Evidência insuficiente';a['result']='Só há entrega posterior';assess(db,'C1',a,'Pesquisa inicial')
    a['justification']='Revisão explicada';assess(db,'C1',a,'Correção')
    assert db.execute('SELECT count(*) FROM assessments').fetchone()[0]==2
    assert db.execute('SELECT previous_id FROM current_assessments').fetchone()[0] is not None
    assert db.execute('SELECT after_exercise FROM evidence').fetchone()[0]==1

def test_covered_period_without_event_cannot_credit_later_government(tmp_path):
    db=connect(tmp_path/'a.sqlite');initialize(db);seed_plans(db);add_commitment(db,record())
    eid=add_evidence(db,dict(commitment_id='C1',title='Relatório',institution='Instituição',url='https://example.org/temer',support='Entrega em 2017',kind='primary',covered_start='2017-01-01',covered_end='2017-12-31'))
    with pytest.raises(ValueError):assess(db,'C1',dict(status='Concluída',result='Entregue',justification='Teste',confidence='Alta',confidence_reason='Documento',cutoff='2016-05-11',evidence_ids=[eid]),'Teste')

def test_reference_from_another_plan_rolls_back(tmp_path):
    db=connect(tmp_path/'a.sqlite');initialize(db);seed_plans(db)
    db.execute("INSERT INTO documents(id,plan_id,sha256,filename,stored_filename,source_url,consulted_at,bytes,pages,metadata) VALUES(1,'2018','hash','a.pdf','a.pdf','https://example.org','2026-10-13',1,1,'{}')")
    db.execute("INSERT INTO pages(document_id,number,text) VALUES(1,1,'Promessa de teste.')");db.commit()
    r=record('2002');r['refs']=[dict(document_id=1,page=1,quote='Promessa de teste.')]
    with pytest.raises(ValueError):add_commitment(db,r)
    assert db.execute('SELECT count(*) FROM commitments').fetchone()[0]==0
