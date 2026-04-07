#!/bin/bash
# Avia ML Service - Run Script
# Usage: ./run.sh [--reload] [--port PORT]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PORT="${PORT:-8100}"
RELOAD=""

# Parse args
for arg in "$@"; do
  case $arg in
    --reload) RELOAD="--reload" ;;
    --port) shift; PORT="$1" ;;
    --port=*) PORT="${arg#*=}" ;;
  esac
done

# Check venv
if [ ! -f "$VENV_DIR/bin/python" ]; then
  echo "Virtual environment not found. Creating..."
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
  "$VENV_DIR/bin/python" -m spacy download en_core_web_sm
fi

# Create .env from example if not present
if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  echo "Created .env from .env.example — edit as needed."
fi

echo "Starting Avia ML Service on port $PORT..."
"$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port "$PORT" $RELOAD
