#!/bin/bash
set -e

# Start local Redis server
echo "Starting background Redis server..."
redis-server --daemonize yes

# Start Celery worker in background
echo "Starting background Celery worker..."
celery -A app.celery_app.celery_app worker --loglevel=info &

# Start FastAPI server
PORT_NUM=${PORT:-8000}
echo "Starting FastAPI uvicorn server on port ${PORT_NUM}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT_NUM}"
