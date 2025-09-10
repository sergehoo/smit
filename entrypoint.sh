#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Boot…"

# --- Attente optionnelle de la DB via socket TCP (sans psycopg2) ---
if [[ -n "${DATABASE_HOST:-}" ]]; then
  DB_HOST="${DATABASE_HOST}"
  DB_PORT="${DATABASE_PORT:-5432}"
  echo "[entrypoint] Waiting for DB ${DB_HOST}:${DB_PORT}…"
  for i in {1..40}; do
    python - <<PY
import socket, os, sys
host=os.environ.get("DATABASE_HOST","localhost")
port=int(os.environ.get("DATABASE_PORT","5432"))
s=socket.socket()
s.settimeout(2)
try:
    s.connect((host, port))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
    if [[ $? -eq 0 ]]; then
      echo "[entrypoint] DB ready."
      break
    fi
    sleep 2
  done
fi

# --- Migrations / collectstatic contrôlés par variables ---
if [[ "${RUN_MIGRATIONS:-0}" == "1" ]]; then
  echo "[entrypoint] manage.py migrate…"
  python manage.py migrate --noinput
fi

if [[ "${RUN_COLLECTSTATIC:-0}" == "1" ]]; then
  echo "[entrypoint] manage.py collectstatic…"
  python manage.py collectstatic --noinput
fi

# --- Ne pas casser les permissions des volumes : simple test d'écriture ---
mkdir -p /smitci-app/media /smitci-app/static || true
if ! sh -lc 'touch /smitci-app/media/.write_test && rm -f /smitci-app/media/.write_test'; then
  echo "[WARN] /smitci-app/media non inscriptible par $(id) – vérifier les volumes/ownership."
fi
if ! sh -lc 'touch /smitci-app/static/.write_test && rm -f /smitci-app/static/.write_test'; then
  echo "[WARN] /smitci-app/static non inscriptible par $(id)."
fi

# --- Si docker-compose fournit une commande, on l'exécute telle quelle ---
if [[ "$#" -gt 0 ]]; then
  echo "[entrypoint] exec: $*"
  exec "$@"
fi

# --- Sinon fallback Gunicorn configurable par env ---
APP_MODULE="${APP_MODULE:-smitci.wsgi:application}"
WORKER_CLASS="${WORKER_CLASS:-sync}"  # pour ASGI: uvicorn.workers.UvicornWorker
BIND="${GUNICORN_BIND:-0.0.0.0:8000}"
OPTS="${GUNICORN_OPTS:---workers 2 --threads 2 --timeout 60 --graceful-timeout 30 --log-level warning}"

echo "[entrypoint] default gunicorn -> ${APP_MODULE} (-k ${WORKER_CLASS})"
exec gunicorn "${APP_MODULE}" -k "${WORKER_CLASS}" --bind "${BIND}" ${OPTS}