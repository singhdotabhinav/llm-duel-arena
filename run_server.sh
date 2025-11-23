#!/bin/bash
# Run the server using the virtual environment

cd "$(dirname "$0")"
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

