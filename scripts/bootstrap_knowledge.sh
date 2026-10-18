#!/usr/bin/env bash
# Restore the saved knowledge without discarding local work. Python stdlib only.
set -euo pipefail
cd "${1:-/workspace/3brown1blue-like-video-generator}"
if [[ ! -f scripts/verify_knowledge.py || ! -f docs/KNOWLEDGE.md ]]; then
  if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
    echo 'Local changes exist; preserved without switching branches.' >&2
    exit 1
  fi
  git fetch origin refs/heads/video/decay-heat-delivery:refs/remotes/origin/video/decay-heat-delivery
  if git show-ref --verify --quiet refs/heads/video/decay-heat-delivery; then
    git switch video/decay-heat-delivery
  else
    git switch --track -c video/decay-heat-delivery origin/video/decay-heat-delivery
  fi
  git merge --ff-only origin/video/decay-heat-delivery
fi
python3 scripts/verify_knowledge.py
