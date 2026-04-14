#!/usr/bin/env bash
set -euo pipefail

exec celery -A config worker \
  --loglevel=info \
  --queues=default,ai_grading \
  --concurrency=2 \
  --max-tasks-per-child=50 \
  --without-gossip \
  --without-mingle