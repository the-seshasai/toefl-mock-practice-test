#!/usr/bin/env bash
# Start the backend (port 8001) and the frontend dev server (port 5173); Ctrl-C stops both.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
BACKEND_PORT=8001   # fixed: the Vite proxy in frontend/vite.config.ts points here, and port 8000 is reserved on this machine
FRONTEND_PORT=5173

[[ -f .env ]] || { cp .env.example .env; echo "Created .env from .env.example"; }
command -v claude >/dev/null || echo "WARNING: 'claude' not found; question generation will fail (see README)."
[[ -f data/piper/en_US-ryan-medium.onnx ]] || echo "WARNING: Piper voices missing; Listening and Speaking will not start. Run scripts/download_models.sh"
[[ -f data/whisper/base.en/model.bin ]] || echo "WARNING: Whisper model missing; Speaking cannot be scored. Run scripts/download_models.sh"
for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
  if ss -ltn "sport = :$port" 2>/dev/null | grep -q LISTEN; then
    echo "ERROR: port $port is already in use." >&2; exit 1
  fi
done

pids=()
cleanup() { for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done; wait 2>/dev/null || true; }
trap cleanup EXIT INT TERM

(cd backend && exec uv run uvicorn app.main:app --port "$BACKEND_PORT") &
pids+=($!)
(cd frontend && exec npm run dev) &
pids+=($!)

for _ in $(seq 1 40); do
  curl -fs "http://127.0.0.1:$BACKEND_PORT/api/health" >/dev/null 2>&1 && break
  sleep 0.5
done
echo
echo "  App:      http://localhost:$FRONTEND_PORT"
echo "  API docs: http://localhost:$BACKEND_PORT/docs"
echo "  Ctrl-C to stop."
wait
