from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
PHONE_NUMBER = os.getenv("MOBILE_PHONE")
OWNER = os.getenv("OWNER")
ADMIN_ID = os.getenv("ADMIN_ID")