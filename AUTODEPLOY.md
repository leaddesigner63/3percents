# Автодеплой: пошаговая настройка

Этот документ описывает, как настроить автодеплой через GitHub Actions для этого репозитория.

## 1. Подготовка сервера
1. Установите зависимости:
   - `python3`
   - `python3-venv`
   - `git`
   - `systemd`
2. Создайте пользователя для деплоя или используйте существующего.
3. Разместите сервисный файл `telegram-carousel-bot.service` и включите сервис:
   ```bash
   sudo cp telegram-carousel-bot.service /etc/systemd/system/telegram-carousel-bot.service
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-carousel-bot.service
   ```
4. Убедитесь, что у сервиса есть доступ к переменным окружения:
   ```bash
   sudo touch /etc/telegram-carousel-bot.env
   sudo chmod 600 /etc/telegram-carousel-bot.env
   sudo chown root:root /etc/telegram-carousel-bot.env
   ```

## 2. Создание ключа для деплоя
1. На машине, где будет храниться ключ (локально), сгенерируйте ключ:
   ```bash
   ssh-keygen -t ed25519 -C "deploy@3percents" -f ./deploy_ed25519
   ```
2. Добавьте публичный ключ на сервер:
   ```bash
   ssh-copy-id -i ./deploy_ed25519.pub user@your-server
   ```
3. Закодируйте приватный ключ в base64:
   ```bash
   base64 -w 0 ./deploy_ed25519 > deploy_ed25519.b64
   ```

## 3. Настройка секретов GitHub
Добавьте в репозиторий следующие secrets:
- `DEPLOY_KEY_B64` — содержимое файла `deploy_ed25519.b64`.
- `DEPLOY_HOST` — адрес сервера (IP/hostname).
- `DEPLOY_PORT` — SSH-порт (например, `22`).
- `DEPLOY_USER` — пользователь для SSH.
- `PROJECT_DIR` — директория проекта на сервере (например, `/opt/3percents`).
- `SERVICE_NAME` — имя systemd сервиса (например, `telegram-carousel-bot`).

## 4. Проверка деплоя
1. Сделайте push в ветку `main`.
2. Откройте GitHub Actions и убедитесь, что workflow `Deploy 3percents` отработал успешно.
3. Проверьте статус сервиса на сервере:
   ```bash
   sudo systemctl status telegram-carousel-bot
   ```

## 5. Диагностика при проблемах
- Проверьте, что `PROJECT_DIR` не пустой и существует.
- Проверьте, что ключи и права доступа корректны.
- Если ручной запуск `./scripts/deploy.sh` сообщает, что `origin` не настроен, добавьте remote:
  ```bash
  git remote add origin https://github.com/<owner>/<repo>.git
  git fetch origin
  ```
- Если GitHub Actions падает с ошибкой `detected dubious ownership`, добавьте каталог в список безопасных:
  ```bash
  git config --global --add safe.directory /opt/3percents
  ```
- Если деплой падает с `python: command not found`, убедитесь, что установлен `python3` и `python3-venv`, а в PATH доступен `python3` (workflow использует `python3 -m venv`).
- Если в `PROJECT_DIR` уже есть файлы без `.git`, деплой заново инициализирует репозиторий, сбросит состояние на `origin/main` и очистит мусорные файлы.
- Проверьте логи сервиса:
  ```bash
  sudo journalctl -u telegram-carousel-bot -n 200 --no-pager
  ```

## 6. Символический пуш для проверки автодеплоя
Если нужно проверить автодеплой без функциональных изменений:
1. Добавьте комментарий или строку в этот файл (например, дата проверки).
2. Сделайте commit и push в ветку `main`.
3. Дождитесь выполнения workflow `Deploy 3percents` в GitHub Actions.
   #
