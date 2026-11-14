#!/bin/sh
set -eu
if [ -z "${CFBENCH_WORKSPACE:-}" ]; then
  echo "CFBENCH_WORKSPACE is not set" >&2
  exit 1
fi
printf '%s\n' 'format_demo_ok' > "${CFBENCH_WORKSPACE}/smoke_marker.txt"
