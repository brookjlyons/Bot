# bot/config.py

import json
import os

# Path to config.json in /data/
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json')

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

# Ensure discord_ids mapping always exists and is a dict
discord_ids = CONFIG.get("discord_ids")
if not isinstance(discord_ids, dict):
    CONFIG["discord_ids"] = {}

# Always ensure webhook_url key exists
CONFIG.setdefault("webhook_url", None)

# Inject Discord webhook from environment secret if enabled
if CONFIG.get("webhook_enabled", False):
    CONFIG["webhook_url"] = os.getenv("DISCORD_WEBHOOK_URL") or None
    if not CONFIG["webhook_url"]:
        print("⚠️  webhook_enabled is True but DISCORD_WEBHOOK_URL is not set. Falling back to console output.")
else:
    CONFIG["webhook_url"] = None

# Enforce test_mode semantics
if CONFIG.get("test_mode", False):
    # In test mode, no posting and no state updates will occur
    CONFIG["webhook_enabled"] = False
    CONFIG["webhook_url"] = None
    print("🧪 Test mode is ON — will not post to Discord or update state.")
