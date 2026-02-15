#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$ROOT_DIR/frontend"
npm install
npm run build

cd "$ROOT_DIR"
python3 -m pip install -r requirements-fastapi.txt
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
