from dotenv import load_dotenv
from openai import AsyncOpenAI
import os

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
AI_TOKEN = os.getenv('AI_TOKEN')
CHANNEL_ID_DAILY = os.getenv('CHANNEL_ID_DAILY')
CHANNEL_ID = os.getenv('CHANNEL_ID')
PHONE_NUMBER = os.getenv("MOBILE_PHONE")
OWNER = os.getenv("OWNER")
ADMIN_ID = [id for id in os.getenv("ADMIN_ID").split(",")]

client = AsyncOpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=AI_TOKEN,
)