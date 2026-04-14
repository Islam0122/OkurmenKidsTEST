#!/usr/bin/env bash
set -e
exec celery -A config beat -l info