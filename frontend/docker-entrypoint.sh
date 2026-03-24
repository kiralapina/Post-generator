#!/bin/sh
set -e
BACKEND_HOST="${BACKEND_HOST:-backend}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

if [ -n "${BACKEND_URL:-}" ]; then
  BACKEND_UPSTREAM=$(echo "${BACKEND_URL}" | sed 's#/*$##')
else
  BACKEND_UPSTREAM="http://${BACKEND_HOST}:${BACKEND_PORT}"
fi

# Host для upstream: у Traefik/HTTPS бэка нужен реальный хост, иначе маршрутизация/SNI ломаются
case "$BACKEND_UPSTREAM" in
  https://*)
    UPSTREAM_HOST=$(echo "$BACKEND_UPSTREAM" | sed -E 's#^https://([^/:]+).*#\1#')
    BACKEND_HOST_HEADER="proxy_set_header Host ${UPSTREAM_HOST};"
    OPTIONAL_PROXY_SSL="proxy_ssl_server_name on; proxy_ssl_protocols TLSv1.2 TLSv1.3; proxy_ssl_verify off;"
    ;;
  http://*)
    BACKEND_HOST_HEADER="proxy_set_header Host \$host;"
    OPTIONAL_PROXY_SSL=""
    ;;
  *)
    BACKEND_HOST_HEADER="proxy_set_header Host \$host;"
    OPTIONAL_PROXY_SSL=""
    ;;
esac

AUTO_NS=$(grep -m1 '^nameserver[[:space:]]' /etc/resolv.conf 2>/dev/null | awk '{print $2}')

if [ -n "${NGINX_RESOLVER:-}" ] && [ "${NGINX_RESOLVER}" != "127.0.0.11" ]; then
  :
elif [ -n "${AUTO_NS}" ]; then
  NGINX_RESOLVER="${AUTO_NS}"
else
  NGINX_RESOLVER="${NGINX_RESOLVER:-127.0.0.11}"
fi

echo "[nginx-entrypoint] BACKEND_UPSTREAM=${BACKEND_UPSTREAM} BACKEND_URL=${BACKEND_URL:-} BACKEND_HOST=${BACKEND_HOST} NGINX_RESOLVER=${NGINX_RESOLVER} (AUTO_NS=${AUTO_NS:-none})" >&2

awk -v u="$BACKEND_UPSTREAM" \
    -v r="$NGINX_RESOLVER" \
    -v hh="$BACKEND_HOST_HEADER" \
    -v ssl="$OPTIONAL_PROXY_SSL" '
{
  gsub("@NGINX_RESOLVER@", r)
  gsub("@BACKEND_UPSTREAM@", u)
  gsub("@BACKEND_HOST_HEADER@", hh)
  gsub("@OPTIONAL_PROXY_SSL@", ssl)
  print
}' /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g "daemon off;"
