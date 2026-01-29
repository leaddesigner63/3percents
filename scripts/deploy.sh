#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-${REPO_DIR}/.venv}"

cd "$REPO_DIR"

current_branch=$(git rev-parse --abbrev-ref HEAD)

git fetch origin

git reset --hard "origin/${current_branch}"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

pip install -r requirements.txt

systemctl restart telegram-carousel-bot
