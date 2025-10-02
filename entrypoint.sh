#!/usr/bin/env bash
set -euo pipefail

# ============== config par défaut (overridable via env) ==============
DB_HOST="${DATABASE_HOST:-smitDB}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_WAIT_MAX_SEC="${DATABASE_WAIT_MAX_SEC:-80}"           # temps total max d'attente DB
DB_WAIT_STEP_SEC="${DATABASE_WAIT_STEP_SEC:-2}"          # intervalle entre essais
DB_SOCKET_TIMEOUT_SEC="${DATABASE_SOCKET_TIMEOUT:-2}"    # timeout connect()

RUN_MIGRATIONS="${RUN_MIGRATIONS:-0}"
RUN_COLLECTSTATIC="${RUN_COLLECTSTATIC:-0}"

APP_MODULE="${APP_MODULE:-smitci.wsgi:application}"
WORKER_CLASS="${WORKER_CLASS:-sync}"               # pour ASGI: uvicorn.workers.UvicornWorker
GUNICORN_BIND="${GUNICORN_BIND:-0.0.0.0:8000}"
GUNICORN_OPTS="${GUNICORN_OPTS:---workers 2 --threads 2 --timeout 60 --graceful-timeout 30 --log-level warning}"

STATIC_ROOT_DIR="${STATIC_ROOT_DIR:-/smitci-app/smitci/staticfiles}" # doit correspondre à settings.STATIC_ROOT
STATIC_MOUNT_DIR="${STATIC_MOUNT_DIR:-/smitci-app/static}"           # volume monté pour servir (si utilisé)
MEDIA_DIR="${MEDIA_DIR:-/smitci-app/media}"

echo "[entrypoint] Boot…"

# ============== gestion signaux ==============
trap 'echo "[entrypoint] Caught SIGTERM"; exit 143' TERM
trap 'echo "[entrypoint] Caught SIGINT";  exit 130' INT

# ============== attente DB (TCP) ==============
if [[ -n "${DB_HOST}" ]]; then
  echo "[entrypoint] Waiting for DB ${DB_HOST}:${DB_PORT}… (max ${DB_WAIT_MAX_SEC}s)"
  SECS=0
  until python - "$DB_HOST" "$DB_PORT" "$DB_SOCKET_TIMEOUT_SEC" >/dev/null 2>&1 <<'PY'
import socket, sys
host=sys.argv[1]; port=int(sys.argv[2]); to=float(sys.argv[3])
s=socket.socket(); s.settimeout(to)
try:
    s.connect((host, port)); s.close(); sys.exit(0)
except Exception:
    sys.exit(1)
PY
  do
    sleep "${DB_WAIT_STEP_SEC}"
    SECS=$((SECS + DB_WAIT_STEP_SEC))
    if (( SECS >= DB_WAIT_MAX_SEC )); then
      echo "[entrypoint][ERROR] DB not reachable after ${DB_WAIT_MAX_SEC}s -> abort."
      exit 1
    fi
  done
  echo "[entrypoint] DB ready."
fi

# ============== migrations / collectstatic (optionnels) ==============
if [[ "${RUN_MIGRATIONS}" == "1" ]]; then
  echo "[entrypoint] manage.py migrate…"
  python manage.py migrate --noinput
fi

if [[ "${RUN_COLLECTSTATIC}" == "1" ]]; then
  echo "[entrypoint] manage.py collectstatic…"
  python manage.py collectstatic --noinput
fi

# ============== vérifs d’écriture (volumes) ==============
mkdir -p "${MEDIA_DIR}" "${STATIC_MOUNT_DIR}" "${STATIC_ROOT_DIR}" || true

if ! sh -lc "touch '${MEDIA_DIR}/.write_test' && rm -f '${MEDIA_DIR}/.write_test'"; then
  echo "[WARN] ${MEDIA_DIR} non inscriptible par $(id -u):$(id -g) – vérifier volumes/ownership."
fi
# si tu sers les static depuis le volume monté
if ! sh -lc "touch '${STATIC_MOUNT_DIR}/.write_test' && rm -f '${STATIC_MOUNT_DIR}/.write_test'"; then
  echo "[WARN] ${STATIC_MOUNT_DIR} non inscriptible – OK si tu n’écris pas ici en prod."
fi
# si STATIC_ROOT (collectstatic) est différent, on teste aussi :
if ! sh -lc "touch '${STATIC_ROOT_DIR}/.write_test' && rm -f '${STATIC_ROOT_DIR}/.write_test'"; then
  echo "[WARN] ${STATIC_ROOT_DIR} non inscriptible – collectstatic pourrait échouer."
fi

# ============== exécuter la commande docker-compose (si fournie) ==============
if [[ "$#" -gt 0 ]]; then
  echo "[entrypoint] exec: $*"
  exec "$@"
fi

# ============== fallback gunicorn ==============
echo "[entrypoint] default gunicorn -> ${APP_MODULE} (-k ${WORKER_CLASS})"
exec gunicorn "${APP_MODULE}" -k "${WORKER_CLASS}" --bind "${GUNICORN_BIND}" ${GUNICORN_OPTS}