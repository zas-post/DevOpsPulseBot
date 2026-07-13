import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_RAW = os.getenv("ADMIN_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not BOT_TOKEN or not ADMIN_ID_RAW or not CHANNEL_ID:
    raise ValueError(
        "Критическая ошибка: Не все переменные окружения заданы в файле .env! "
        "Проверьте BOT_TOKEN, ADMIN_ID и CHANNEL_ID."
    )

try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except ValueError:
    raise ValueError("Критическая ошибка: ADMIN_ID в файле .env должен быть числом!")

DATABASE_URL = "sqlite+aiosqlite:///bot_database.db"
