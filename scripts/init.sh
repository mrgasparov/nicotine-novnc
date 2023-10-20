#! /bin/bash

set -e

PGID=${PGID:-0}
PUID=${PUID:-0}

umask "${UMASK:-0000}"

if [ "$PGID" -ne 0 ] && [ "$PUID" -ne 0 ]; then
  groupmod -o -g "$PGID" nicotine
  usermod -o -u "$PUID" nicotine
  chown -R nicotine:nicotine /data
fi

[ -n "$TZ" ] && [ -f "/usr/share/zoneinfo/$TZ" ] && ln -sf "/usr/share/zoneinfo/$TZ" /etc/localtime

RESOLUTION=${RESOLUTION:-"1280x720"}
export NOVNC_PORT=${NOVNC_PORT:-"6080"}
export USERNAME=$(getent passwd "$PUID" | cut -d: -f1)

supervisor_conf="/etc/supervisord.conf"
template=$(<"$supervisor_conf")
result=$(echo "$template" | envsubst)
exec echo "$result" > $supervisor_conf
