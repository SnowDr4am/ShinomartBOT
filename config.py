import os
from dotenv import load_dotenv
from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage
from aiogram import Bot, Dispatcher

load_dotenv()

# Old
# BOT_TOKEN = os.getenv('BOT_TOKEN')
AI_TOKEN = os.getenv('AI_TOKEN')
CHANNEL_ID_DAILY = os.getenv('CHANNEL_ID_DAILY')
CHANNEL_ID = os.getenv('CHANNEL_ID')
TIRES_AND_DISCS_CHANNEL = os.getenv("TIRES_AND_DISCS_CHANNEL")
PHONE_NUMBER = os.getenv("MOBILE_PHONE")
OWNER = os.getenv("OWNER")
ADMIN_ID = [id for id in os.getenv("ADMIN_ID").split(",")]


# New

# --- Загрузка переменных окружения ---
load_dotenv()

# --- Конфигурация базы данных ---
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")

# --- Конфигурация бота ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Конфигурация Redis ---
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "1"))

redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD or None,
    db=REDIS_DB,
    decode_responses=True,
)

storage = RedisStorage(redis=redis_client)

# --- Инициализация бота ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)