import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")
ADMINS = os.getenv("ADMINS", "").split(",")
TECH_SUPPORT_ID = os.getenv("TECH_SUPPORT_ID")
START_VIDEO_URL = os.getenv("START_VIDEO_URL")
DB_CHAT_ID = os.getenv("DB_CHAT_ID")
