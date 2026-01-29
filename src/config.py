import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    channel_id: str
    data_file: str


def load_config() -> Config:
    load_dotenv()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    channel_id = os.getenv("CHANNEL_ID", "").strip()
    data_file = os.getenv("DATA_FILE", "/var/lib/telegram-carousel-bot/posts.json").strip()

    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")
    if bot_token == "your-telegram-bot-token":
        raise ValueError(
            "TELEGRAM_BOT_TOKEN содержит пример значения. "
            "Задайте реальный токен в .env или /etc/telegram-carousel-bot.env"
        )
    if not channel_id:
        raise ValueError("CHANNEL_ID is required")

    return Config(bot_token=bot_token, channel_id=channel_id, data_file=data_file)
