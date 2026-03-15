import os
from pathlib import Path

BASE_URL = "https://sattacademy.com"
LOGIN_URL = f"{BASE_URL}/login"

# Browser profile directory for persistent login
PROFILE_DIR = os.path.join(Path.home(), ".crawl4ai", "profiles", "satt_academy")

# Dhaka University category ID
DHAKA_UNIVERSITY_CATEGORY_ID = 95
DHAKA_UNIVERSITY_SLUG = "dhaka-university"

# University categories mapping (for future expansion)
UNIVERSITY_CATEGORIES = {
    "dhaka-university": 95,
    "chittagong-university": 96,
    "rajshahi-university": 97,
    "jagannath-university": 98,
    "jahangirnagar-university": 99,
    "barishal-university": 100,
    "khulna-university": 101,
    "comilla-university": 102,
    "begum-rokeya-university": 103,
}

# Scraping settings
REQUEST_DELAY_MIN = 3.0   # minimum seconds between requests
REQUEST_DELAY_MAX = 6.0   # maximum seconds between requests (randomized)
BACKOFF_BASE = 30         # seconds to wait after a connection error before retry
BACKOFF_MAX = 300         # max backoff (5 minutes)
MAX_RETRIES = 3
COOLDOWN_AFTER_ERRORS = 60  # seconds to cool down after consecutive failures
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "satt_academy_admission"
)
