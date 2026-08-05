"Utility module to initialize logger and load files."

import json
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)


TEMPLATE = {
    "requests": {
        "timeout": 10,
        "max_concurrent_requests": 1,
        "recheck_interval": 15,
        "max_retries": 5,
        "retry_delay": 5,
    },
    "targeted_website": {
        "endpoint": "https://pk-gr-services.gvcworld.eu/api/v1/periodslot/slots",
        "auth_token": "TOKEN",
    },
    "proxy": {
        "http": "PROXY ADDRESS",
        "https": "PROXY ADDRESS",
    },
    "telegram": {
        "bot_token": "BOT TOKEN",
        "dev_chat_id": "5766884382",
        "users_chat_ids": [],
    },
    "dates": ["05/09/2026"],
    "date_range": {"enabled": False, "start": "01/09/2026", "end": "30/09/2026"},
}


def load_config(path="config.json"):
    "load config file"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(TEMPLATE, f, indent=4)
        return TEMPLATE

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_cookies(path="request_data/cookies.json"):
    "load cookies file"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_headers(path="request_data/headers.json"):
    "load headers file"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_payload(path="request_data/payload.json"):
    "load payload file"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data, path="config.json"):
    "Save config file"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


CONFIG = load_config()
COOKIES = load_cookies()
HEADERS = load_headers()
PAYLOAD = load_payload()
