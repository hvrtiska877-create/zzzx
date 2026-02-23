#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <github_repo_url> [branch]"
  echo "Example: $0 git@github.com:yourname/SMART.git main"
  exit 1
fi

REPO_URL="$1"
BRANCH="${2:-main}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not inside a git repo." >&2
  exit 1
fi

if ! git remote | grep -q '^origin$'; then
  git remote add origin "$REPO_URL"
else
  git remote set-url origin "$REPO_URL"
fi

git push -u origin "$BRANCH"

echo "Pushed to $REPO_URL on branch $BRANCH"
