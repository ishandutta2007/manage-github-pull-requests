import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("ADMIN_TOKEN")
API_URL = "https://api.github.com"
CACHE_DIR = ".cache"
CACHE_EXPIRATION_HOURS = 24
