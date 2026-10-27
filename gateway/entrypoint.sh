#!/bin/sh
set -eu

export DOLLAR='$'
envsubst '${REACT_UPSTREAM} ${NEXT_UPSTREAM} ${API_UPSTREAM} ${DOLLAR}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
