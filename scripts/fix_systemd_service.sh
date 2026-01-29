#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="${SERVICE_NAME:-telegram-carousel-bot}"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
VENV_DIR="${VENV_DIR:-${REPO_DIR}/.venv}"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

if [ ! -f "${REPO_DIR}/telegram-carousel-bot.service" ]; then
  echo "ERROR: не найден unit-шаблон ${REPO_DIR}/telegram-carousel-bot.service" >&2
  exit 1
fi

rendered_unit="$(mktemp)"
trap 'rm -f "$rendered_unit"' EXIT

sed \
  -e "s|^WorkingDirectory=.*|WorkingDirectory=${REPO_DIR}|" \
  -e "s|^ExecStart=.*|ExecStart=${VENV_DIR}/bin/python -m src.bot|" \
  "${REPO_DIR}/telegram-carousel-bot.service" > "${rendered_unit}"

if [ -w "$UNIT_PATH" ] || [ -w "$(dirname "$UNIT_PATH")" ]; then
  cp "$rendered_unit" "$UNIT_PATH"
  systemctl daemon-reload
elif command -v sudo >/dev/null 2>&1 && sudo -n true; then
  sudo cp "$rendered_unit" "$UNIT_PATH"
  sudo systemctl daemon-reload
else
  echo "ERROR: нет прав на обновление ${UNIT_PATH}. Запустите от root или через sudo." >&2
  exit 1
fi

if command -v sudo >/dev/null 2>&1 && ! [ "$(id -u)" -eq 0 ]; then
  sudo systemctl restart "$SERVICE_NAME"
else
  systemctl restart "$SERVICE_NAME"
fi

systemctl status "$SERVICE_NAME" --no-pager -l
