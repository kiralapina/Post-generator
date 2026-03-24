#!/bin/sh
set -e
BACKEND_HOST="${BACKEND_HOST:-backend}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

# NGINX_RESOLVER: в Docker обычно 127.0.0.11; в K8s/Dokploy — первый nameserver из resolv.conf
if [ -z "${NGINX_RESOLVER:-}" ]; then
  NGINX_RESOLVER=$(grep -m1 '^nameserver[[:space:]]' /etc/resolv.conf 2>/dev/null | awk '{print $2}')
fi
NGINX_RESOLVER="${NGINX_RESOLVER:-127.0.0.11}"

echo "[nginx-entrypoint] BACKEND_HOST=${BACKEND_HOST} BACKEND_PORT=${BACKEND_PORT} NGINX_RESOLVER=${NGINX_RESOLVER}" >&2

sed \
  -e "s#@BACKEND_HOST@#${BACKEND_HOST}#g" \
  -e "s#@BACKEND_PORT@#${BACKEND_PORT}#g" \
  -e "s#@NGINX_RESOLVER@#${NGINX_RESOLVER}#g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
