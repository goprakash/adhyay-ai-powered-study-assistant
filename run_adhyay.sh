#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "========================================================"
echo "    📖 Welcome to Adhyay — React + FastAPI Edition     "
echo "========================================================"

# Check Python 3.10
if [ -x "/opt/homebrew/bin/python3.10" ]; then
    PY_BIN="/opt/homebrew/bin/python3.10"
elif command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
else
    echo "Error: Python 3 not found."
    exit 1
fi

# 1. Virtual environment & backend dependencies
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    $PY_BIN -m venv venv
fi
source venv/bin/activate

echo "[2/4] Ensuring Python & FastAPI dependencies..."
pip install -q fastapi uvicorn python-multipart pdfplumber google-genai python-dotenv

# 2. Frontend dependencies
echo "[3/4] Ensuring React & npm dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
fi
cd ..

# 3. Seed demo data
cd backend
python -c "import database; database.init_db(); database.seed_demo_data(force=False)"
cd ..

# 4. Cleanup any previous runs on ports 8000 & 5173
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true

echo "========================================================"
echo "  🚀 Starting FastAPI backend on http://localhost:8000 "
echo "  🌐 Starting React frontend on http://localhost:5173  "
echo "========================================================"

# Trap SIGINT/SIGTERM to kill child processes
cleanup() {
    echo ""
    echo "Shutting down Adhyay services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start backend
(cd backend && ../venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!

# Wait briefly for backend to initialize
sleep 2

# Start frontend
(cd frontend && npm run dev -- --host 127.0.0.1 --port 5173) &
FRONTEND_PID=$!

wait
