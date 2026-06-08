import os
import json
import time
from datetime import datetime, timedelta
from .config import CACHE_DIR, CACHE_EXPIRATION_HOURS

def get_cache_path(category, identifier):
    clean_id = identifier.replace("/", "_")
    return os.path.join(CACHE_DIR, category, f"{clean_id}.json")

def is_cache_valid(cache_path):
    if not os.path.exists(cache_path):
        return False
    
    try:
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
            timestamp = cache_data.get("timestamp", 0)
            cache_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - cache_time < timedelta(hours=CACHE_EXPIRATION_HOURS):
                return True
    except (json.JSONDecodeError, KeyError):
        pass
    return False

def save_to_cache(category, identifier, data):
    cache_path = get_cache_path(category, identifier)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    cache_data = {
        "timestamp": time.time(),
        "data": data
    }
    with open(cache_path, 'w') as f:
        json.dump(cache_data, f, indent=2)

def load_from_cache(category, identifier):
    cache_path = get_cache_path(category, identifier)
    with open(cache_path, 'r') as f:
        return json.load(f)["data"]

def clear_cache(category, identifier):
    cache_path = get_cache_path(category, identifier)
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
        except OSError:
            pass
