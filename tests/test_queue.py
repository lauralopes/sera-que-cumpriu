import time
from backend.db import connect,initialize
from backend.queue import enqueue,claim,finish,control

def test_queue_persistence_pause_cancel_and_expired_lease(tmp_path):
    path=tmp_path/'a.sqlite';db=connect(path);initialize(db)
    tid=enqueue(db,'fetch','u1',{'url':'https://example.org'})
    assert enqueue(db,'fetch','u1',{})==tid
    control(db,'pause'); assert claim(db,'one') is None
    control(db,'resume'); assert claim(db,'one')['id']==tid
    db.execute('UPDATE tasks SET lease_until=? WHERE id=?',(time.time()-1,tid));db.commit();db.close()
    db=connect(path); assert claim(db,'two')['id']==tid
    finish(db,tid,'two',{'ok':1});assert claim(db,'one') is None
    t2=enqueue(db,'fetch','u2',{});control(db,'cancel',t2);assert claim(db,'one') is None
