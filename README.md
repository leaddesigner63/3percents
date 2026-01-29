# Telegram Channel Carousel Bot

Бот показывает сообщения канала (со второго по предпоследнее) по одному на экран и использует инлайн‑клавиатуру для навигации.

## Настройка

1. Скопируйте/отредактируйте файл `.env` и укажите значения:
   - `TELEGRAM_BOT_TOKEN` — токен бота.
   - `CHANNEL_ID` — username канала (например `@volshebniye_tri_procenta`) или числовой ID.
   - `DATA_FILE` — путь к JSON для хранения постов.
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python -m src.bot
```

Бот получает новые посты через `channel_post` и сохраняет их. При `/start` бот показывает доступные посты в карусели.

## Systemd

Сервисный файл можно разместить, например, в `/etc/systemd/system/telegram-carousel-bot.service`, а переменные окружения — в `/etc/telegram-carousel-bot.env`. Пример unit-файла есть в репозитории: `telegram-carousel-bot.service`.

После установки unit-файла выполните:

```bash
systemctl daemon-reload
systemctl enable telegram-carousel-bot
systemctl start telegram-carousel-bot
systemctl status telegram-carousel-bot
```

## Деплой

Для обновления кода, зависимостей и перезапуска сервиса используйте скрипт:

```bash
./scripts/deploy.sh
```

Скрипт делает `git fetch` + `git reset --hard origin/<текущая-ветка>`, создаёт/обновляет venv в `.venv`, устанавливает зависимости и выполняет `systemctl restart telegram-carousel-bot`. При необходимости запускайте с правами, позволяющими выполнять `systemctl` (например, через `sudo`). 
