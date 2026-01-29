# Telegram Channel Carousel Bot

Бот показывает сообщения канала (со второго по предпоследнее) по одному на экран и использует инлайн‑клавиатуру для навигации.

## Структура проекта и точное расположение файлов

- `src/bot.py` — основной модуль бота.
- `src/config.py` — загрузка конфигурации из переменных окружения.
- `src/storage.py` — хранение и фильтрация постов.
- `scripts/deploy.sh` — ручной деплой (pull/reset + venv + зависимости + restart systemd).
- `scripts/fix_systemd_service.sh` — исправление unit-файла systemd по фактическому пути проекта.
- `.github/workflows/deploy.yml` — workflow автодеплоя GitHub Actions.
- `telegram-carousel-bot.service` — unit-файл systemd (копируется в `/etc/systemd/system/telegram-carousel-bot.service`).
- `.env.example` — шаблон переменных окружения для локального запуска.
- `AUTODEPLOY.md` — пошаговая инструкция по настройке автодеплоя.

## Настройка

1. Создайте директорию для данных:
   ```bash
   sudo mkdir -p /var/lib/telegram-carousel-bot
   sudo chown -R root:root /var/lib/telegram-carousel-bot
   sudo chmod 700 /var/lib/telegram-carousel-bot
   ```
2. Создайте файл окружения для systemd и заполните его точными значениями:
   ```bash
   sudo tee /etc/telegram-carousel-bot.env >/dev/null <<'EOF'
   TELEGRAM_BOT_TOKEN=ваш_токен_бота
   CHANNEL_ID=@volshebniye_tri_procenta
   DATA_FILE=/var/lib/telegram-carousel-bot/posts.json
   EOF
   sudo chmod 600 /etc/telegram-carousel-bot.env
   sudo chown root:root /etc/telegram-carousel-bot.env
   ```
   Замените `TELEGRAM_BOT_TOKEN` и `CHANNEL_ID` на реальные значения вашего бота и канала.
3. Скопируйте шаблон `.env.example` в `.env` и продублируйте те же значения для локального запуска:
   ```bash
   cp .env.example .env
   ```
   Затем отредактируйте `.env`, чтобы он совпадал с `/etc/telegram-carousel-bot.env`.
4. Создайте виртуальное окружение внутри репозитория и установите зависимости:
   ```bash
   python3 -m venv .venv
   ./.venv/bin/pip install -r requirements.txt
   ```

## Запуск

```bash
./.venv/bin/python -m src.bot
```

Бот получает новые посты через `channel_post` и сохраняет их. При `/start` бот показывает доступные посты в карусели.

## Systemd

Разместите сервисный файл в `/etc/systemd/system/telegram-carousel-bot.service`, а переменные окружения — в `/etc/telegram-carousel-bot.env`. Unit-файл лежит в репозитории: `telegram-carousel-bot.service`.

После установки unit-файла выполните:

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-carousel-bot
sudo systemctl start telegram-carousel-bot
sudo systemctl status telegram-carousel-bot
```

## Деплой

Для обновления кода, зависимостей и перезапуска сервиса используйте скрипт:

```bash
./scripts/deploy.sh
```

Скрипт делает `git fetch` + `git reset --hard origin/<текущая-ветка>`, создаёт/обновляет venv в `.venv`, устанавливает зависимости и выполняет `systemctl restart telegram-carousel-bot`. При необходимости запускайте с правами, позволяющими выполнять `systemctl` (например, через `sudo`).

## Автодеплой

Автодеплой настраивается через GitHub Actions workflow `.github/workflows/deploy.yml`. Пошаговая инструкция со всеми точными путями и командами находится в `AUTODEPLOY.md` — используйте её без отклонений.
