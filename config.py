import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Credentials
API_ID = int(os.getenv("API_ID", "0").strip().strip('"').strip("'"))
API_HASH = os.getenv("API_HASH", "").strip().strip('"').strip("'")
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip().strip('"').strip("'")
SESSION_STRING = os.getenv("SESSION_STRING", "").strip().strip('"').strip("'")

# Admin & Owner
OWNER_ID = int(os.getenv("OWNER_ID", "0").strip().strip('"').strip("'"))

# Bot Details
BOT_NAME = os.getenv("BOT_NAME", "HarmoniX")
COMMAND_PREFIXES = os.getenv("COMMAND_PREFIXES", "/ !").split()

# Group Features
WELCOME_ENABLED = os.getenv("WELCOME_ENABLED", "true").lower() in ("true", "1", "yes")

# Default Welcome Template
DEFAULT_WELCOME_MESSAGE = (
    "👋 Welcome {mention} to **{title}**!\n\n"
    "✨ We're glad to have you here.\n"
    "👥 Total Members: `{count}`"
)

# Promotions & Official Links
SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "").strip()
UPDATES_CHANNEL = os.getenv("UPDATES_CHANNEL", "").strip()
PROMO_TEXT = os.getenv("PROMO_TEXT", "✨ Powered by HarmoniX | SPIDYxSTREAM").strip()
PROMO_URL = os.getenv("PROMO_URL", "").strip()
