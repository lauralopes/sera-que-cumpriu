import pytest
from backend.db import connect,initialize
from backend.ingest import seed_plans
from backend.research import add_commitment,revise_criterion,assess

def test_criterion_change_keeps_history_and_invalid_dates_fail(tmp_path):
    db=connect(tmp_path/'a.sqlite');initialize(db);seed_plans(db)
    add_commitment(db,dict(id='X',plan_id='2018',theme='Economia',description='Promessa',nature='ação',criterion='Primeiro',criterion_set_at='2026-10-13'))
    revise_criterion(db,'X','Novo critério','Refinamento antes da pesquisa','Codex')
    assert db.execute('SELECT criterion FROM commitments').fetchone()[0]=='Novo critério'
    old=db.execute('SELECT previous_criterion FROM criterion_history').fetchone()[0]
    assert old=='Primeiro'
    with pytest.raises(ValueError):assess(db,'X',dict(status='Evidência insuficiente',result='pendente',justification='Faltam dados',confidence='Baixa',confidence_reason='Faltam fontes',cutoff='2021-99-10',evidence_ids=[]),'Teste')

def test_returning_to_old_criterion_does_not_reactivate_assessment(tmp_path):
    from backend.research import add_evidence,list_commitments
    from backend.metrics import summaries
    db=connect(tmp_path/'b.sqlite');initialize(db);seed_plans(db)
    add_commitment(db,dict(id='X',plan_id='2018',theme='Economia',description='Promessa',nature='ação',criterion='A',criterion_set_at='2026-10-13'))
    eid=add_evidence(db,dict(commitment_id='X',title='Fonte',institution='Instituição',url='https://example.org/a',support='Entrega',kind='primary',event_date='2020-01-01'))
    assess(db,'X',dict(status='Concluída',result='Entregue',justification='Fonte',confidence='Alta',confidence_reason='Fonte',cutoff='2022-12-31',evidence_ids=[eid]),'Inicial')
    revise_criterion(db,'X','B','Mudança');revise_criterion(db,'X','A','Retorno')
    assert list_commitments(db)[0]['status']=='Requer revisão'
    assert next(s for s in summaries(db) if s['id']=='2018')['completed']==0
