#!/usr/bin/env zsh
# One-shot launcher: starts FastAPI backend and serves the Reddit frontend.
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT_DIR"

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-5500}

if [[ ! -f .env ]]; then
  echo "[!] Missing .env in $ROOT_DIR (needs REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT)."
  exit 1
fi

if ! command -v uvicorn >/dev/null 2>&1; then
  echo "[!] uvicorn not found. Install deps (e.g., pip install -r requirements.txt)."
  exit 1
fi

cleanup() {
  [[ -n ${UVICORN_PID:-} ]] && kill "$UVICORN_PID" 2>/dev/null || true
  [[ -n ${HTTP_PID:-} ]] && kill "$HTTP_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[+] Starting FastAPI backend on port $BACKEND_PORT ..."
UVICORN_CMD=(uvicorn api.main:app --reload --port "$BACKEND_PORT" --log-level info)
"${UVICORN_CMD[@]}" &
UVICORN_PID=$!

cd "$ROOT_DIR/frontend"
echo "[+] Serving frontend on port $FRONTEND_PORT ..."
python -m http.server "$FRONTEND_PORT" >/dev/null 2>&1 &
HTTP_PID=$!

sleep 1
echo "[+] Opening browser..."
open "http://localhost:${FRONTEND_PORT}/reddit.html" >/dev/null 2>&1 || true

echo "[+] Running. Press Ctrl+C to stop both backend and frontend."
wait
