#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-${REPO_DIR}/.venv}"

cd "$REPO_DIR"

current_branch=$(git rev-parse --abbrev-ref HEAD)
ENV_FILE="${ENV_FILE:-/etc/telegram-carousel-bot.env}"
DATA_FILE_PATH=""
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  DATA_FILE_PATH="${DATA_FILE:-}"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git fetch origin
  git reset --hard "origin/${current_branch}"
  if [ -n "$DATA_FILE_PATH" ] && [[ "$DATA_FILE_PATH" == "$REPO_DIR/"* ]]; then
    data_rel="${DATA_FILE_PATH#$REPO_DIR/}"
    git clean -fdx -e "$data_rel"
  else
    git clean -fdx
  fi
else
  echo "WARNING: remote 'origin' не настроен, пропускаю git fetch/reset." >&2
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

pip install -r requirements.txt

SERVICE_NAME="${SERVICE_NAME:-telegram-carousel-bot}"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
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

if command -v systemctl >/dev/null 2>&1; then
  if [ -f "$UNIT_PATH" ] || systemctl list-unit-files --type=service --no-legend | awk '{print $1}' | grep -qx "${SERVICE_NAME}.service"; then
    if command -v sudo >/dev/null 2>&1 && ! [ "$(id -u)" -eq 0 ]; then
      sudo systemctl restart "${SERVICE_NAME}"
    else
      systemctl restart "${SERVICE_NAME}"
    fi
  else
    echo "WARNING: systemd unit ${SERVICE_NAME}.service не найден, пропускаю рестарт." >&2
  fi
else
  echo "WARNING: systemctl не найден, пропускаю рестарт сервиса ${SERVICE_NAME}." >&2
fi
