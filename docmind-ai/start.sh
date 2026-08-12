#!/bin/sh
set -e

alembic upgrade head

# solo pool: no forked child processes, tasks run sequentially in this one
# process. Free tier gives us 512Mi total; prefork (the default) would spawn
# extra worker sub-processes we don't need for a low-traffic demo app.
celery -A app.workers.celery_app worker --loglevel=info --pool=solo &
CELERY_PID=$!

uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" &
WEB_PID=$!

# Exit (so Render notices and restarts the container) as soon as either
# process dies. Written in POSIX sh, not bash — "wait -n" isn't portable to
# dash, which is /bin/sh on the python:3.13-slim base image.
while kill -0 "$CELERY_PID" 2>/dev/null && kill -0 "$WEB_PID" 2>/dev/null; do
    sleep 2
done

exit 1
