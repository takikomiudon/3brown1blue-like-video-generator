#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec docker run --rm --network none \
  --mount "type=bind,src=$PWD,dst=/manim" \
  --mount type=bind,src=/usr/share/fonts/opentype/noto,dst=/usr/local/share/fonts/noto,readonly \
  --user "$(id -u):$(id -g)" -w /manim \
  -e XDG_CACHE_HOME=/tmp/cache -e MPLCONFIGDIR=/tmp/matplotlib \
  decay-heat-manim:0.20.1 "$@"
