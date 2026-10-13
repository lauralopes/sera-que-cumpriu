import pytest
from backend.archive import validate_public_url,parse_snapshot

def test_unsafe_urls_rejected():
    for u in ['http://localhost/a','http://127.0.0.1','http://[::1]','file:///etc/passwd','https://169.254.169.254','https://user:pass@example.org']:
        with pytest.raises(ValueError):validate_public_url(u)

def test_snapshot_timestamp_is_not_requested_date():
    r=parse_snapshot({'archived_snapshots':{'closest':{'available':True,'timestamp':'20050101000000','url':'http://web.archive.org/web/20050101000000/http://example.org','status':'200'}}},'20041231')
    assert r['timestamp']=='20050101000000' and r['requested_timestamp']=='20041231'
    assert r['available'] and r['exact_date'] is False
