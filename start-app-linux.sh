#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- frontend build (skip if npm missing) ---
cd "$ROOT_DIR/frontend"
if command -v npm >/dev/null 2>&1; then
  echo "Installing frontend dependencies..."
  npm ci --no-audit --no-fund || npm install
  echo "Building frontend..."
  npm run build
else
  echo "npm not found — skipping frontend build"
fi

# --- backend: use a virtualenv to avoid system-wide pip installs ---
cd "$ROOT_DIR"
PYTHON_CMD=python3
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  echo "python3 not found in PATH — aborting" >&2
  exit 1
fi

# Prefer an already activated venv; otherwise use/create project .venv
if [ -n "${VIRTUAL_ENV:-}" ]; then
  echo "Using activated virtualenv: $VIRTUAL_ENV"
  PY="$PYTHON_CMD"
else
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PY="$ROOT_DIR/.venv/bin/python"
    echo "Using existing .venv at $ROOT_DIR/.venv"
  else
    echo "Creating virtualenv at $ROOT_DIR/.venv"
    "$PYTHON_CMD" -m venv "$ROOT_DIR/.venv"
    PY="$ROOT_DIR/.venv/bin/python"
  fi
fi

# Install backend requirements into the selected environment
echo "Installing Python dependencies into environment: $("$PY" -V 2>&1)"
"$PY" -m pip install --upgrade pip setuptools wheel
"$PY" -m pip install -r requirements-fastapi.txt

# Start the app with the chosen python (exec replaces the shell with the process)
echo "Starting uvicorn (http://0.0.0.0:8000)..."
exec "$PY" -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

