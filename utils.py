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
        "max_retries": 3,
        "retry_delay": 10,
    },
    "targeted_website": {
        "endpoint": "https://pk-gr-services.gvcworld.eu/api/v1/periodslot/slots",
        "auth_token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJjb2xkc2hlbGwiLCJyb2xlIjoiUk9MRV9BUFBMSUNBTlQiLCJpc3MiOiJndmN3LWFwcCIsImV4cCI6MTc4Njc3NDg2NSwiaWF0IjoxNzg0OTc0ODY1LCJqdGkiOiJlNmU1OWEwNy1mZWI0LTQ4NTctYmZmYi1iNTRkZjcyNzNlOTIifQ.A6jCq6f3zaIXdFzD4Yrcc5j8-ayIrz1lXMlnhc3IMtg",
    },
    "proxy": {
        "http": "http://fmuarmnh-PK-rotate:eydwqjv99lmf@p.webshare.io:80",
        "https": "http://fmuarmnh-PK-rotate:eydwqjv99lmf@p.webshare.io:80",
    },
    "telegram": {
        "bot_token": "8420930196:AAF_9DsVI-algZ6qjWHMM6i5ZvGIA58FMwQ",
        "dev_chat_id": "5766884382",
        "users_chat_ids": ["8966549582"],
    },
    "dates": [],
    "date_range": {"enabled": True, "start": "01/09/2026", "end": "30/09/2026"},
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
