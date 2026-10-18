#!/usr/bin/env bash
# Restore the saved knowledge without discarding local work. Python stdlib only.
set -euo pipefail
cd "${1:-/workspace/3brown1blue-like-video-generator}"
if [[ ! -f scripts/verify_knowledge.py || ! -f docs/KNOWLEDGE.md ]]; then
  if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
    echo 'Local changes exist; preserved without switching branches.' >&2
    exit 1
  fi
  git fetch origin refs/heads/main:refs/remotes/origin/main
  if git show-ref --verify --quiet refs/heads/main; then
    git switch main
  else
    # --single-branch clones do not map this remote branch for tracking.
    git switch --no-track -c main origin/main
  fi
  git merge --ff-only origin/main
fi
python3 scripts/verify_knowledge.py
