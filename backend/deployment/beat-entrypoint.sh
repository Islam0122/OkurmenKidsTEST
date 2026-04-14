#!/usr/bin/env bash
set -euo pipefail

exec celery -A config beat \
  --loglevel=info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler