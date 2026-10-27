#!/bin/sh
set -eu

commit_sha=${SOURCE_COMMIT:-unknown}
case "$commit_sha" in
  *[!0-9a-f]*|'') commit_sha=unknown ;;
esac

printf '{"commit_sha":"%s"}\n' "$commit_sha" > /usr/share/nginx/html/version.json
