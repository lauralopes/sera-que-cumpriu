#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${AUDIT_PYTHON:-.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then PYTHON=python3; fi
PORT="${AUDIT_PORT:-8765}"
status=0
"$PYTHON" - "$PORT" <<'PORT_CHECK' || status=$?
import json,socket,sys,urllib.request
try:
    port=int(sys.argv[1])
    if not 1<=port<=65535:raise ValueError()
except ValueError:
    print("AUDIT_PORT deve ser um número entre 1 e 65535.",file=sys.stderr);sys.exit(12)
try:
    with socket.create_connection(("127.0.0.1",port),timeout=2):pass
except ConnectionRefusedError:sys.exit(0)
except OSError:
    print("Não foi possível verificar a porta local.",file=sys.stderr);sys.exit(12)
try:
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(f"http://127.0.0.1:{port}/api/plans",timeout=3) as response:
        plans=json.loads(response.read(100000))
    expected={2002,2006,2010,2014,2018,2022}
    same=isinstance(plans,list) and {p.get("election") for p in plans}==expected and all(str(p.get("election"))==p.get("id") for p in plans)
except Exception:same=False
if same:
    print(f"O aplicativo já está em execução. Abra http://127.0.0.1:{port}");sys.exit(10)
print(f"A porta {port} está ocupada por outro serviço. Use AUDIT_PORT=8766 ./scripts/start.sh",file=sys.stderr)
sys.exit(11)
PORT_CHECK
if [[ "$status" == 10 ]]; then exit 0; fi
if [[ "$status" != 0 ]]; then exit "$status"; fi
if [[ ! -f frontend/dist/index.html ]]; then npm --prefix frontend ci; npm --prefix frontend run build; fi
"$PYTHON" -m backend.worker &
worker_pid=$!
cleanup() { kill "$worker_pid" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
"$PYTHON" -m uvicorn backend.api:app --host 127.0.0.1 --port "$PORT"
