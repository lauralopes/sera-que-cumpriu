from .research import STATES, DETERMINED, list_commitments

def compute_summary(rows, extraction_complete):
    states={s:sum(r.get('status')==s for r in rows) for s in STATES}
    measurable=[r for r in rows if r['measurable']]
    n=len(measurable)
    completed=sum(r.get('status')=='Concluída' for r in measurable)
    determined=sum(r.get('status') in DETERMINED for r in measurable)
    researched=sum(r['research_state']=='assessed' for r in measurable)
    return dict(total=len(rows),measurable=n,completed=completed,determined=determined,
                principal_percent=round(100*completed/n,1) if n else None,
                determined_percent=round(100*completed/determined,1) if determined else None,
                coverage_percent=round(100*researched/n,1) if n else None,
                researched=researched,pending=sum(r['research_state']!='assessed' for r in rows),
                excluded_determined=len(rows)-determined,states=states,partial_universe=not extraction_complete)

def summaries(db):
    rows=list_commitments(db); result=[]
    for p in db.execute('SELECT * FROM plans ORDER BY election'):
        s=dict(p);s.update(compute_summary([r for r in rows if r['plan_id']==p['id']],p['extraction_complete']))
        page=db.execute('SELECT count(*) total,coalesce(sum(extraction_reviewed),0) reviewed FROM pages pg JOIN documents d ON d.id=pg.document_id WHERE d.plan_id=?',(p['id'],)).fetchone()
        s['pages_total']=page['total'];s['pages_reviewed']=page['reviewed'];result.append(s)
    return result
