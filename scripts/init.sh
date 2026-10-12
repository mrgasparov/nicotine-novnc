#! /bin/bash

set -euo pipefail

PGID=${PGID:-0}
PUID=${PUID:-0}

umask "${UMASK:-0000}"

gtk_config_dir="/data/.config/gtk-4.0"
mkdir -p "$gtk_config_dir"
if [ ! -e "$gtk_config_dir/gtk.css" ] && [ ! -L "$gtk_config_dir/gtk.css" ]; then
  cp /etc/nicotine/gtk.css "$gtk_config_dir/gtk.css"
fi

if [ "$PGID" -ne 0 ] && [ "$PUID" -ne 0 ]; then
  groupmod -o -g "$PGID" nicotine
  usermod -o -u "$PUID" nicotine
  chown -R nicotine:nicotine /data
fi

if [ -n "${TZ:-}" ] && [ -f "/usr/share/zoneinfo/$TZ" ]; then
  ln -sf "/usr/share/zoneinfo/$TZ" /etc/localtime
fi

export RESOLUTION=${RESOLUTION:-"1280x720"}
export NOVNC_PORT=${NOVNC_PORT:-"6080"}
USERNAME=$(getent passwd "$PUID" | cut -d: -f1)
export USERNAME

supervisor_conf="/tmp/supervisord.conf"
envsubst '${USERNAME} ${RESOLUTION} ${NOVNC_PORT} ${PIPX_HOME}' \
  < /etc/supervisord.conf.template > "$supervisor_conf"

exec supervisord -c "$supervisor_conf"
