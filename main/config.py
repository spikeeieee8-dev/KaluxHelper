"""
KaluxHost Bot Configuration
All global constants live here. Nothing else imports from outside this file.
"""
import os
from dotenv import load_dotenv  # Add this
load_dotenv()

# ── Bot ───────────────────────────────────────────────────────────────────────
DEFAULT_PREFIX     = "!"
BOT_NAME           = "KaluxHost"
BOT_VERSION        = "2.0.0"

# ── Token (from environment) ──────────────────────────────────────────────────
TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN is not set in environment secrets.")

# ── Embed Colours ─────────────────────────────────────────────────────────────
COLOR_BRAND   = 0x5865F2   # KaluxHost purple-blue
COLOR_SUCCESS = 0x57F287   # Green
COLOR_ERROR   = 0xED4245   # Red
COLOR_WARN    = 0xFEE75C   # Yellow
COLOR_INFO    = 0x5DADE2   # Light blue

# ── Paths ─────────────────────────────────────────────────────────────────────
import pathlib
ROOT_DIR    = pathlib.Path(__file__).parent.parent   # artifacts/discord-bot/
DATA_DIR    = ROOT_DIR / "data"
MODULES_DIR = ROOT_DIR / "modules"
DB_PATH     = DATA_DIR / "kaluxhost.db"

DATA_DIR.mkdir(exist_ok=True)
