import os
import json
from utils import DATA_DIR, logger

CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

DEFAULT_CONFIG = {
    "token": "",
    "username": "",
    "active_repo": "",
    "default_branch": "main",
    "default_folder": "",
    "retry_count": 3,
    "timeout": 30,
    "theme": "default",
    "zip_compression": False,
    "parallel_upload": True
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            # Merge with defaults for missing keys
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        # Set restrictive permissions on config file (owner read/write only)
        os.chmod(CONFIG_FILE, 0o600)
    except Exception as e:
        logger.error(f"Error saving config: {e}")

def get_config(key, default=None):
    config = load_config()
    return config.get(key, default)

def set_config(key, value):
    config = load_config()
    config[key] = value
    save_config(config)
