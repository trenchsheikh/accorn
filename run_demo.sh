#!/bin/bash
echo "Starting Acorn Server..."
echo "Once started, visit http://localhost:8000/demo to test the widget."
export DATABASE_URL="sqlite:///./demo.db"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
