from dotenv import load_dotenv
from pathlib import Path
import os
from database.models import BotSettings
from cogs.System.settings import get_botsettings, set_botsettings


BASE_DIR = Path(__file__).resolve().parent
COGS_DIR = os.path.join(BASE_DIR, "cogs")

ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

GPT_API = os.getenv("GPT_API")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
        raise ValueError("Database URL not found in environment")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

RENDER = os.getenv("RENDER")
