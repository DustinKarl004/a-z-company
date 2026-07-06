#!/usr/bin/env bash
# Runs the backend (FastAPI) and frontend (Vite) dev servers together.
#
# Ports are chosen to avoid clashing with anything else already running on
# this machine (e.g. port 8000 is occupied by an unrelated app) — override
# with BACKEND_PORT / FRONTEND_PORT env vars if these ever collide too.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_PORT="${BACKEND_PORT:-8123}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

check_port_free() {
  local port="$1"
  local label="$2"
  if lsof -i ":$port" >/dev/null 2>&1; then
    echo "Port $port is already in use (needed for $label)." >&2
    echo "Something else on this machine is using it — set ${label}_PORT to a free port and re-run." >&2
    exit 1
  fi
}

check_port_free "$BACKEND_PORT" "BACKEND"
check_port_free "$FRONTEND_PORT" "FRONTEND"

if [ ! -d "$BACKEND_DIR/.venv" ]; then
  echo "backend/.venv not found. Run this first:" >&2
  echo "  cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "frontend/node_modules not found. Run this first:" >&2
  echo "  cd frontend && npm install" >&2
  exit 1
fi

pids=()
cleanup() {
  echo
  echo "Stopping dev servers..."
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting backend on http://127.0.0.1:$BACKEND_PORT ..."
(
  cd "$BACKEND_DIR"
  source .venv/bin/activate
  exec uvicorn app.main:app --reload --port "$BACKEND_PORT"
) &
pids+=("$!")

echo "Starting frontend on http://localhost:$FRONTEND_PORT ..."
(
  cd "$FRONTEND_DIR"
  export VITE_API_BASE_URL="http://127.0.0.1:$BACKEND_PORT"
  exec npm run dev -- --port "$FRONTEND_PORT"
) &
pids+=("$!")

wait
