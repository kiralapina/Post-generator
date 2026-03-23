#!/usr/bin/env bash
# =============================================================================
# Обновление контейнеров с Docker Hub: pull образов lapiki/backend и lapiki/frontend,
# при изменении digest — docker compose up -d.
#
# Установка на сервере:
#   chmod +x update-containers.sh
#   ./update-containers.sh
#
# Cron (каждый час) — см. crontab.example
# Требуется: docker compose v2 (плагин), bash, доступ к Docker Hub.
# =============================================================================

set -euo pipefail

# Каталог, где лежит этот скрипт и docker-compose.yml
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

log() {
  echo "[$(date -Iseconds)] $*"
}

# Подхватываем DOCKERHUB_USER, IMAGE_TAG и т.д. из .env рядом с compose
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -z "${DOCKERHUB_USER:-}" ]]; then
  log "ОШИБКА: задайте DOCKERHUB_USER в файле $SCRIPT_DIR/.env (ник Docker Hub)."
  exit 1
fi

TAG="${IMAGE_TAG:-latest}"
BACKEND_REF="${DOCKERHUB_USER}/backend:${TAG}"
FRONTEND_REF="${DOCKERHUB_USER}/frontend:${TAG}"

log "Проект: $SCRIPT_DIR, compose: $COMPOSE_FILE"
log "Образы: $BACKEND_REF, $FRONTEND_REF"

# ID локальных образов до pull (если образа ещё не было — none)
id_backend_before=$(docker image inspect "$BACKEND_REF" --format '{{.Id}}' 2>/dev/null || echo "none")
id_frontend_before=$(docker image inspect "$FRONTEND_REF" --format '{{.Id}}' 2>/dev/null || echo "none")

log "docker compose pull — загрузка слоёв с Docker Hub..."
docker compose -f "$COMPOSE_FILE" pull

id_backend_after=$(docker image inspect "$BACKEND_REF" --format '{{.Id}}' 2>/dev/null || echo "none")
id_frontend_after=$(docker image inspect "$FRONTEND_REF" --format '{{.Id}}' 2>/dev/null || echo "none")

bk_updated=0
fe_updated=0

if [[ "$id_backend_before" != "$id_backend_after" ]]; then
  log "backend: образ обновлён (изменился слой / digest)."
  bk_updated=1
else
  log "backend: без изменений после pull (уже актуальный или тот же digest)."
fi

if [[ "$id_frontend_before" != "$id_frontend_after" ]]; then
  log "frontend: образ обновлён (изменился слой / digest)."
  fe_updated=1
else
  log "frontend: без изменений после pull (уже актуальный или тот же digest)."
fi

if [[ "$bk_updated" -eq 1 || "$fe_updated" -eq 1 ]]; then
  log "docker compose up -d — пересоздание контейнеров при необходимости..."
  docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
  log "Готово: контейнеры соответствуют новым образам."
else
  log "Образы не изменились: контейнеры не пересоздаём (экономия времени)."
  log "Подсказка: принудительный перезапуск — docker compose -f $COMPOSE_FILE up -d --force-recreate"
fi

log "Конец."
