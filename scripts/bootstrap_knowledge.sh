#!/usr/bin/env bash
# Refresh main even when an older snapshot already contains documentation.
set -euo pipefail
cd "${1:-/workspace/3brown1blue-like-video-generator}"
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  echo 'Local changes preserved. Automatic refresh was not run; inspect HEAD and current voice settings before production.' >&2
  exit 2
fi
git fetch origin refs/heads/main
if [[ "$(git branch --show-current)" != main ]]; then
  if git show-ref --verify --quiet refs/heads/main; then
    git switch main
  else
    git switch --no-track -c main FETCH_HEAD
  fi
fi
git merge --ff-only FETCH_HEAD
python3 scripts/verify_knowledge.py
python3 -m unittest discover -s .agents/skills/science-explainer/scripts -p test_voicevox_audio.py
