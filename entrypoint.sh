#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${DATABASE_HOST:-smitDB}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_WAIT_MAX_SEC="${DATABASE_WAIT_MAX_SEC:-80}"
DB_WAIT_STEP_SEC="${DATABASE_WAIT_STEP_SEC:-2}"

RUN_MIGRATIONS="${RUN_MIGRATIONS:-0}"
RUN_COLLECTSTATIC="${RUN_COLLECTSTATIC:-0}"

APP_MODULE="${APP_MODULE:-smitci.wsgi:application}"
WORKER_CLASS="${WORKER_CLASS:-sync}"
GUNICORN_BIND="${GUNICORN_BIND:-0.0.0.0:8000}"
GUNICORN_OPTS="${GUNICORN_OPTS:---workers 2 --threads 2 --timeout 60 --graceful-timeout 30 --log-level warning}"

STATIC_ROOT_DIR="${STATIC_ROOT_DIR:-/smitci-app/smitci/staticfiles}"
MEDIA_DIR="${MEDIA_DIR:-/smitci-app/media}"

echo "[entrypoint] Boot…"

trap 'echo "[entrypoint] Caught SIGTERM"; exit 143' TERM
trap 'echo "[entrypoint] Caught SIGINT";  exit 130' INT

# ==== Attente DB via pg_isready (léger, sans python -) ====
if [[ -n "${DB_HOST}" ]]; then
  echo "[entrypoint] Waiting for DB ${DB_HOST}:${DB_PORT}… (max ${DB_WAIT_MAX_SEC}s)"
  SECS=0
  until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" >/dev/null 2>&1; do
    sleep "${DB_WAIT_STEP_SEC}"
    SECS=$((SECS + DB_WAIT_STEP_SEC))
    if (( SECS >= DB_WAIT_MAX_SEC )); then
      echo "[entrypoint][ERROR] DB not reachable after ${DB_WAIT_MAX_SEC}s -> abort."
      exit 1
    fi
  done
  echo "[entrypoint] DB ready."
fi

# ==== Migrations (optionnelles) ====
if [[ "${RUN_MIGRATIONS}" == "1" ]]; then
  echo "[entrypoint] manage.py migrate…"
  python manage.py migrate --noinput
fi

# ==== collectstatic (désactivé en prod car fait à la build) ====
if [[ "${RUN_COLLECTSTATIC}" == "1" ]]; then
  echo "[entrypoint] manage.py collectstatic…"
  python manage.py collectstatic --noinput
fi

# ==== Vérifs écriture ====
mkdir -p "${MEDIA_DIR}" "${STATIC_ROOT_DIR}" || true
if ! sh -lc "touch '${MEDIA_DIR}/.write_test' && rm -f '${MEDIA_DIR}/.write_test'"; then
  echo "[WARN] ${MEDIA_DIR} non inscriptible – vérifier volumes/ownership."
fi
if ! sh -lc "touch '${STATIC_ROOT_DIR}/.write_test' && rm -f '${STATIC_ROOT_DIR}/.write_test'"; then
  echo "[WARN] ${STATIC_ROOT_DIR} non inscriptible – OK si statics déjà build."
fi

# ==== Exécuter la commande docker-compose si fournie ====
if [[ "$#" -gt 0 ]]; then
  echo "[entrypoint] exec: $*"
  exec "$@"
fi

# ==== Fallback gunicorn ====
echo "[entrypoint] default gunicorn -> ${APP_MODULE} (-k ${WORKER_CLASS})"
exec gunicorn "${APP_MODULE}" -k "${WORKER_CLASS}" --bind "${GUNICORN_BIND}" ${GUNICORN_OPTS}