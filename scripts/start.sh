#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${AUDIT_PYTHON:-.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then PYTHON=python3; fi
if [[ ! -f frontend/dist/index.html ]]; then npm --prefix frontend ci; npm --prefix frontend run build; fi
"$PYTHON" -m backend.worker &
worker_pid=$!
cleanup() { kill "$worker_pid" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
"$PYTHON" -m uvicorn backend.api:app --host 127.0.0.1 --port "${AUDIT_PORT:-8765}"
