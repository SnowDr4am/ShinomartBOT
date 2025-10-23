import os
from dotenv import load_dotenv
from redis.asyncio import Redis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

# === Загрузка .env ===
load_dotenv()

# === Основные токены и параметры ===
BOT_TOKEN: str = os.getenv("BOT_TOKEN")
AI_TOKEN: str = os.getenv("AI_TOKEN")

# === Каналы ===
CHANNEL_ID_DAILY: str = os.getenv("CHANNEL_ID_DAILY")
CHANNEL_ID: str = os.getenv("CHANNEL_ID")
TIRES_AND_DISCS_CHANNEL: str = os.getenv("TIRES_AND_DISCS_CHANNEL")

# === Контакты / Админы ===
PHONE_NUMBER: str = os.getenv("MOBILE_PHONE")
OWNER: str = os.getenv("OWNER")
ADMIN_ID: list[int] = [int(i.strip()) for i in os.getenv("ADMIN_ID", "").split(",") if i.strip().isdigit()]

# === Redis настройки ===
REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD")
REDIS_PORT: int | None = os.getenv("REDIS_PORT")

redis_client = Redis(
    host="127.0.0.1",
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=1,
    decode_responses=True,
)

storage = RedisStorage(redis=redis_client)

# === Инициализация бота ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)