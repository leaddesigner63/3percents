#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-${REPO_DIR}/.venv}"

cd "$REPO_DIR"

current_branch=$(git rev-parse --abbrev-ref HEAD)

if git remote get-url origin >/dev/null 2>&1; then
  git fetch origin
  git reset --hard "origin/${current_branch}"
else
  echo "WARNING: remote 'origin' не настроен, пропускаю git fetch/reset." >&2
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

pip install -r requirements.txt

UNIT_PATH="/etc/systemd/system/telegram-carousel-bot.service"
if [ -f "$REPO_DIR/telegram-carousel-bot.service" ]; then
  rendered_unit="$(mktemp)"
  sed \
    -e "s|^WorkingDirectory=.*|WorkingDirectory=${REPO_DIR}|" \
    -e "s|^ExecStart=.*|ExecStart=${VENV_DIR}/bin/python -m src.bot|" \
    "$REPO_DIR/telegram-carousel-bot.service" > "$rendered_unit"
  if [ -w "$UNIT_PATH" ] || [ -w "$(dirname "$UNIT_PATH")" ]; then
    cp "$rendered_unit" "$UNIT_PATH"
    systemctl daemon-reload
  elif command -v sudo >/dev/null 2>&1 && sudo -n true; then
    sudo cp "$rendered_unit" "$UNIT_PATH"
    sudo systemctl daemon-reload
  else
    echo "WARNING: нет прав на обновление systemd unit-файла (${UNIT_PATH})." >&2
  fi
  rm -f "$rendered_unit"
fi

if command -v sudo >/dev/null 2>&1 && ! [ "$(id -u)" -eq 0 ]; then
  sudo systemctl restart telegram-carousel-bot
else
  systemctl restart telegram-carousel-bot
fi
