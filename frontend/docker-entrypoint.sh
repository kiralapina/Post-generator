#!/bin/sh
set -e
BACKEND_HOST="${BACKEND_HOST:-backend}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

# Первый nameserver из resolv.conf (в K8s/Dokploy часто не 127.0.0.11)
AUTO_NS=$(grep -m1 '^nameserver[[:space:]]' /etc/resolv.conf 2>/dev/null | awk '{print $2}')

# Явный NGINX_RESOLVER (не дефолт Docker) — не трогаем.
# Иначе: env часто задаёт 127.0.0.11, тогда nginx не резолвит backend вне классического Docker DNS.
if [ -n "${NGINX_RESOLVER:-}" ] && [ "${NGINX_RESOLVER}" != "127.0.0.11" ]; then
  :
elif [ -n "${AUTO_NS}" ]; then
  NGINX_RESOLVER="${AUTO_NS}"
else
  NGINX_RESOLVER="${NGINX_RESOLVER:-127.0.0.11}"
fi

echo "[nginx-entrypoint] BACKEND_HOST=${BACKEND_HOST} BACKEND_PORT=${BACKEND_PORT} NGINX_RESOLVER=${NGINX_RESOLVER} (AUTO_NS=${AUTO_NS:-none})" >&2

sed \
  -e "s#@BACKEND_HOST@#${BACKEND_HOST}#g" \
  -e "s#@BACKEND_PORT@#${BACKEND_PORT}#g" \
  -e "s#@NGINX_RESOLVER@#${NGINX_RESOLVER}#g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
