#!/bin/bash

set -euo pipefail

# Supervisor priority controls launch order, not X server readiness.
for attempt in {1..30}; do
  if xdpyinfo -display :1 >/dev/null 2>&1; then
    exec x0vncserver -display :1 -rfbport 5901 -localhost -SecurityTypes None
  fi
  sleep 1
done

echo "X display :1 did not become ready within 30 seconds" >&2
exit 1
