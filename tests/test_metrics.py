from backend.metrics import compute_summary

def test_denominators_and_missing_are_not_failure():
    rows=[dict(measurable=1,status=s,research_state='assessed') for s in ['Concluída','Parcialmente concluída','Não concluída','Revertida','Evidência insuficiente','Prazo ainda não vencido','Requer revisão']]
    rows += [dict(measurable=1,status=None,research_state='pending'),dict(measurable=0,status='Não mensurável',research_state='assessed')]
    s=compute_summary(rows,False)
    assert s['measurable']==8 and s['completed']==1 and s['principal_percent']==12.5
    assert s['determined']==4 and s['determined_percent']==25.0
    assert s['pending']==1 and s['excluded_determined']==5
    assert s['partial_universe'] is True
    assert s['states']['Não concluída']==1

def test_empty_denominator_is_null():
    assert compute_summary([],False)['principal_percent'] is None
