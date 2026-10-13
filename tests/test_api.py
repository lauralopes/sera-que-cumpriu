from fastapi.testclient import TestClient
from backend.api import create_app
from backend.db import connect,initialize
from backend.ingest import seed_plans

def test_readonly_api_and_mutation_origin(tmp_path):
    path=tmp_path/'a.sqlite';db=connect(path);initialize(db);seed_plans(db);db.close()
    app=create_app(path);client=TestClient(app,base_url='http://127.0.0.1')
    assert len(client.get('/api/plans').json())==6
    assert client.get('/api/commitments').json()==[]
    assert client.post('/api/queue/control',json={'action':'pause'}).status_code==403
    assert client.post('/api/queue/control',json={'action':'invalid'},headers={'X-Audit-Client':'local-browser'}).status_code==422
    assert client.post('/api/queue/control',json={'action':'pause'},headers={'X-Audit-Client':'local-browser','Origin':'https://evil.example'}).status_code==403
    assert client.post('/api/queue/control',json={'action':'pause'},headers={'X-Audit-Client':'local-browser'}).status_code==200
    assert client.get('/api/progress').json()['paused'] is True

def test_foreign_host_is_rejected_even_when_origin_matches(tmp_path):
    client=TestClient(create_app(tmp_path/'b.sqlite'),base_url='http://127.0.0.1')
    assert client.get('/api/plans',headers={'Host':'evil.example'}).status_code==400
    assert client.post('/api/queue/control',json={'action':'pause'},headers={'Host':'evil.example','Origin':'http://evil.example','X-Audit-Client':'local-browser'}).status_code==400
