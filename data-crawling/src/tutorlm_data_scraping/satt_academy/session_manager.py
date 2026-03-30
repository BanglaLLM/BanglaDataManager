"""
Browser session manager for Satt Academy.

Loads cookies either from:
  1. A JSON file (satt_cookies.json) — for servers without a browser
  2. The user's Brave browser via browser_cookie3 — for local dev

Injects them into crawl4ai's AsyncWebCrawler for authenticated scraping.
"""

import json
import os

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from .config import BASE_URL

# Look for cookies file relative to the project root
COOKIES_FILE_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "satt_cookies.json"),
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "satt_cookies.json"),
    os.path.expanduser("~/satt_cookies.json"),
    "satt_cookies.json",
]


def load_cookies_from_file() -> list[dict] | None:
    """Try to load cookies from a JSON file."""
    for path in COOKIES_FILE_CANDIDATES:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            print(f"[COOKIES] Loading from file: {abs_path}")
            with open(abs_path, "r") as f:
                cookies = json.load(f)
            if cookies:
                return cookies
    return None


def extract_brave_cookies(domain: str = "sattacademy.com") -> list[dict]:
    """Extract cookies from the user's Brave browser."""
    try:
        import browser_cookie3
    except ImportError:
        raise RuntimeError(
            "browser_cookie3 not installed and no satt_cookies.json found.\n"
            "Either: pip install browser_cookie3, or provide a satt_cookies.json file."
        )

    print(f"[COOKIES] Extracting cookies for {domain} from Brave browser...")
    try:
        cj = browser_cookie3.brave(domain_name=domain)
    except Exception as e:
        raise RuntimeError(
            f"Failed to extract Brave cookies: {e}\n"
            "Make sure Brave is installed and you're logged into sattacademy.com"
        )

    cookies = []
    for c in cj:
        cookie = {
            "name": c.name,
            "value": c.value,
            "domain": c.domain or f".{domain}",
            "path": c.path or "/",
        }
        if c.secure:
            cookie["secure"] = True
        cookies.append(cookie)

    return cookies


def get_cookies() -> list[dict]:
    """
    Get Satt Academy cookies. Tries JSON file first, then Brave browser.
    """
    # 1. Try JSON file (works on servers)
    cookies = load_cookies_from_file()
    if cookies:
        cookie_names = {c["name"] for c in cookies}
        essential = {"XSRF-TOKEN", "satt_academy_session"}
        missing = essential - cookie_names
        if missing:
            print(f"[COOKIES] WARNING: Missing essential cookies in file: {missing}")
        else:
            print(f"[COOKIES] Loaded {len(cookies)} cookies from file (session cookies found)")
        return cookies

    # 2. Fall back to Brave browser extraction (local dev)
    cookies = extract_brave_cookies()
    if not cookies:
        raise RuntimeError(
            "No cookies found. Either:\n"
            "  - Place a satt_cookies.json in the project root, or\n"
            "  - Log in to sattacademy.com in Brave browser"
        )

    cookie_names = {c["name"] for c in cookies}
    essential = {"XSRF-TOKEN", "satt_academy_session"}
    missing = essential - cookie_names
    if missing:
        print(f"[COOKIES] WARNING: Missing essential cookies: {missing}")
    else:
        print(f"[COOKIES] Extracted {len(cookies)} cookies from Brave")

    return cookies


def get_browser_config(headless: bool = True) -> BrowserConfig:
    """Get BrowserConfig with cookies injected for authenticated scraping."""
    cookies = get_cookies()

    return BrowserConfig(
        browser_type="chromium",
        headless=headless,
        cookies=cookies,
        verbose=False,
        extra_args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--no-sandbox",
        ],
    )


def get_crawl_config(**overrides) -> CrawlerRunConfig:
    """Get default CrawlerRunConfig for Satt Academy pages."""
    defaults = {
        "wait_until": "domcontentloaded",
        "page_timeout": 60000,
        "delay_before_return_html": 1.5,
        "verbose": False,
    }
    defaults.update(overrides)
    return CrawlerRunConfig(**defaults)


async def verify_session() -> bool:
    """Verify cookies can access authenticated Satt Academy pages."""
    print("[VERIFY] Checking if session is valid...")

    browser_config = get_browser_config(headless=True)
    crawl_config = get_crawl_config()

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=f"{BASE_URL}/admission/category/dhaka-university",
                config=crawl_config,
            )

            if result.success:
                html = result.html or ""
                if "data-subcat_id" in html:
                    print("[VERIFY] Session is valid! Can access admission data.")
                    return True
                elif "/login" in (result.redirected_url or result.url or ""):
                    print("[VERIFY] Redirected to login. Session expired.")
                    print("[VERIFY] Update satt_cookies.json with fresh cookies.")
                    return False

            print("[VERIFY] Could not verify. Page loaded but data not found.")
            return False
    except Exception as e:
        print(f"[VERIFY] Error: {e}")
        return False
