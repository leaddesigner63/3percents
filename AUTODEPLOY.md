# Автодеплой: пошаговая настройка

Этот документ описывает, как настроить автодеплой через GitHub Actions для этого репозитория.

## 1. Клонирование репозитория на сервер
1. Подключитесь к серверу по SSH:
   ```bash
   ssh user@your-server
   ```
2. Создайте директорию под проект и назначьте владельца:
   ```bash
   sudo mkdir -p /opt/3percents
   sudo chown -R user:user /opt/3percents
   ```
3. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/<owner>/<repo>.git /opt/3percents
   ```
4. Перейдите в каталог проекта и проверьте ветку:
   ```bash
   cd /opt/3percents
   git checkout main
   git status
   ```
5. Если Git сообщает о «dubious ownership», добавьте каталог в список безопасных:
   ```bash
   git config --global --add safe.directory /opt/3percents
   ```

## 2. Подготовка сервера
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
   Убедитесь, что в unit-файле указан актуальный путь:
   - `WorkingDirectory=/opt/3percents`
   - `ExecStart=/opt/3percents/.venv/bin/python -m src.bot`
   Скрипты деплоя дополнительно переписывают unit-файл, подставляя фактический `PROJECT_DIR`.
4. Убедитесь, что у сервиса есть доступ к переменным окружения:
   ```bash
   sudo touch /etc/telegram-carousel-bot.env
   sudo chmod 600 /etc/telegram-carousel-bot.env
   sudo chown root:root /etc/telegram-carousel-bot.env
   ```
5. Заполните файл окружения реальными значениями:
   ```bash
   sudo tee /etc/telegram-carousel-bot.env >/dev/null <<'EOF'
   TELEGRAM_BOT_TOKEN=ваш_токен_бота
   CHANNEL_ID=@volshebniye_tri_procenta
   DATA_FILE=/var/lib/telegram-carousel-bot/posts.json
   EOF
   ```
6. Создайте директорию для данных и выдайте права:
   ```bash
   sudo mkdir -p /var/lib/telegram-carousel-bot
   sudo chown -R root:root /var/lib/telegram-carousel-bot
   sudo chmod 700 /var/lib/telegram-carousel-bot
   ```

## 3. Создание ключа для деплоя
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

## 4. Настройка секретов GitHub
Добавьте в репозиторий следующие secrets:
- `DEPLOY_KEY_B64` — содержимое файла `deploy_ed25519.b64`.
- `DEPLOY_HOST` — адрес сервера (IP/hostname).
- `DEPLOY_PORT` — SSH-порт (например, `22`).
- `DEPLOY_USER` — пользователь для SSH.
- `PROJECT_DIR` — директория проекта на сервере (например, `/opt/3percents`).
- `SERVICE_NAME` — имя systemd сервиса (например, `telegram-carousel-bot`).
  Если секрет не задан, workflow использует значение по умолчанию `telegram-carousel-bot`.

## 5. Проверка деплоя
1. Сделайте push в ветку `main`.
2. Откройте GitHub Actions и убедитесь, что workflow `Deploy 3percents` отработал успешно.
3. Проверьте статус сервиса на сервере:
   ```bash
   sudo systemctl status telegram-carousel-bot
   ```

## 6. Диагностика при проблемах
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
- Если systemd сообщает `status=203/EXEC`, проверьте, что файл `<PROJECT_DIR>/.venv/bin/python` существует и unit-файл указывает корректный путь (`ExecStart=... -m src.bot`).
- Если при деплое видно `Unit ... not found`, убедитесь, что unit-файл установлен и имя в `SERVICE_NAME` совпадает с фактическим сервисом. При отсутствии unit-файла рестарт пропускается и деплой завершится с предупреждением.
- Если unit-файл указывает на старый путь (например, `/opt/3procenta/venv/bin/python -m bot.main`), выполните скрипт ремонта:
  ```bash
  ./scripts/fix_systemd_service.sh
  ```
  При необходимости запустите с `sudo` и/или передайте переменные `SERVICE_NAME` и `VENV_DIR`.
- Если в `PROJECT_DIR` уже есть файлы без `.git`, деплой заново инициализирует репозиторий, сбросит состояние на `origin/main` и очистит мусорные файлы.
- Проверьте логи сервиса:
  ```bash
  sudo journalctl -u telegram-carousel-bot -n 200 --no-pager
  ```

## 7. Символический пуш для проверки автодеплоя
Если нужно проверить автодеплой без функциональных изменений:
1. Добавьте комментарий или строку в этот файл (например, дата проверки).
2. Сделайте commit и push в ветку `main`.
3. Дождитесь выполнения workflow `Deploy 3percents` в GitHub Actions.
   
