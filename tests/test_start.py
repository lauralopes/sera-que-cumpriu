import json,os,subprocess,sys,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

def test_start_reuses_existing_app_without_launching_another_worker():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200);self.end_headers()
            self.wfile.write(json.dumps([{'id':str(y),'election':y} for y in [2002,2006,2010,2014,2018,2022]]).encode())
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        root=Path(__file__).resolve().parent.parent
        result=subprocess.run(['bash',str(root/'scripts/start.sh')],env={**os.environ,'AUDIT_PORT':str(server.server_port),'AUDIT_PYTHON':sys.executable},capture_output=True,text=True,timeout=10)
        assert result.returncode==0,result.stderr
        assert 'já está em execução' in result.stdout
        assert 'Started server' not in result.stderr
    finally:server.shutdown();server.server_close()
