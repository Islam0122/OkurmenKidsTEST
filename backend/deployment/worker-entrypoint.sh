#!/usr/bin/env bash
set -e
if ! id -u celeryuser >/dev/null 2>&1; then
    useradd -m celeryuser
fi

exec su celeryuser -c "celery -A config beat --scheduler django_celery_beat.schedulers:DatabaseScheduler"