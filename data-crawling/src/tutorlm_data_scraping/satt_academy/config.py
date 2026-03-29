import os
from pathlib import Path

BASE_URL = "https://sattacademy.com"
LOGIN_URL = f"{BASE_URL}/login"

# Browser profile directory for persistent login
PROFILE_DIR = os.path.join(Path.home(), ".crawl4ai", "profiles", "satt_academy")

# All university/institution categories: slug -> category_id
# Slugs match the URL path at sattacademy.com/admission/category/<slug>
UNIVERSITY_CATEGORIES = {
    "dhaka-university": 95,
    "chittagong-university": 96,
    "rajshahi-university": 97,
    "jagannath-university": 98,
    "jahangirnagar-university": 99,
    "barishal-university": 100,
    "khulna-university": 101,
    "cumilla-university": 102,
    "begum-rokeya-university": 103,
    "kazi-nazrul-islam-university": 104,
    "islamic-university": 105,
    "sust": 106,
    "mbstu": 107,
    "nstu": 108,
    "hstu": 109,
    "pstu": 110,
    "pust": 111,
    "just": 112,
    "bsmrstu": 113,
    "buet": 114,
    "kuet": 115,
    "cuet": 116,
    "ruet": 117,
    "sylhet-agricultural-university": 118,
    "shere-bangla-agricultural-university": 119,
    "bangladesh-agricultural-university": 120,
    "bsmrau": 121,
    "mat": 122,
    "dat": 123,
    "cvasu": 124,
    "gucch-biswbidzalygst": 137,
    "bup": 163,
    "bangladesh-marine-academy": 164,
    "nursing-admission-test": 165,
    "engineering-cluster-admission-test": 166,
    "agriculture-cluster-admission-test": 174,
    "national-university": 176,
    "integrated-naval-rating-admission-test": 177,
}

DEFAULT_UNIVERSITY_SLUG = "dhaka-university"

# Scraping settings
REQUEST_DELAY_MIN = 3.0     # minimum seconds between requests
REQUEST_DELAY_MAX = 6.0     # maximum seconds between requests (randomized)
BACKOFF_BASE = 30           # seconds to wait after a connection error before retry
BACKOFF_MAX = 300           # max backoff (5 minutes)
MAX_RETRIES = 3
COOLDOWN_AFTER_ERRORS = 60  # seconds to cool down after consecutive failures
COOLDOWN_BETWEEN_UNIS = 30  # seconds to pause between universities in --all mode
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "satt_academy_admission"
)
