#!/bin/sh
set -eu
printf '{"commit_sha":"%s"}\n' "${SOURCE_COMMIT:-unknown}" > /usr/share/nginx/html/version.json
