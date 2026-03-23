#!/bin/sh
set -e
BACKEND_HOST="${BACKEND_HOST:-backend}"
NGINX_RESOLVER="${NGINX_RESOLVER:-127.0.0.11}"
sed \
  -e "s#@BACKEND_HOST@#${BACKEND_HOST}#g" \
  -e "s#@NGINX_RESOLVER@#${NGINX_RESOLVER}#g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
