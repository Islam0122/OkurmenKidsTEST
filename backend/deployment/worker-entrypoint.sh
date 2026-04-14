#!/usr/bin/env bash
set -e
if ! id -u celeryuser >/dev/null 2>&1; then
    useradd -m celeryuser
fi

exec su celeryuser -c "celery -A config worker -l info --concurrency=2"