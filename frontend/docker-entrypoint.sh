#!/bin/sh
set -e
BACKEND_HOST="${BACKEND_HOST:-backend}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

# Полный URL API (предпочтительно в Dokploy, если сервис не называется «backend» или в другом стеке)
if [ -n "${BACKEND_URL:-}" ]; then
  BACKEND_UPSTREAM=$(echo "${BACKEND_URL}" | sed 's#/*$##')
else
  BACKEND_UPSTREAM="http://${BACKEND_HOST}:${BACKEND_PORT}"
fi

AUTO_NS=$(grep -m1 '^nameserver[[:space:]]' /etc/resolv.conf 2>/dev/null | awk '{print $2}')

if [ -n "${NGINX_RESOLVER:-}" ] && [ "${NGINX_RESOLVER}" != "127.0.0.11" ]; then
  :
elif [ -n "${AUTO_NS}" ]; then
  NGINX_RESOLVER="${AUTO_NS}"
else
  NGINX_RESOLVER="${NGINX_RESOLVER:-127.0.0.11}"
fi

echo "[nginx-entrypoint] BACKEND_UPSTREAM=${BACKEND_UPSTREAM} BACKEND_URL=${BACKEND_URL:-} BACKEND_HOST=${BACKEND_HOST} NGINX_RESOLVER=${NGINX_RESOLVER} (AUTO_NS=${AUTO_NS:-none})" >&2

awk -v u="$BACKEND_UPSTREAM" -v r="$NGINX_RESOLVER" '
{
  gsub("@NGINX_RESOLVER@", r)
  gsub("@BACKEND_UPSTREAM@", u)
  print
}' /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g "daemon off;"
