"""
Browser session manager for Satt Academy.

Extracts cookies from the user's Brave browser (already logged in)
using browser_cookie3 and injects them into crawl4ai's AsyncWebCrawler.
Handles Cloudflare and Google OAuth transparently since cookies are reused.
"""

import browser_cookie3
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from .config import BASE_URL


def extract_brave_cookies(domain: str = "sattacademy.com") -> list[dict]:
    """
    Extract cookies from the user's running Brave browser for the given domain.
    Returns cookies in the format crawl4ai/Playwright expects.
    """
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
        if c.has_nonstandard_attr("HttpOnly") or c.name in ("satt_academy_session",):
            cookie["httpOnly"] = True

        cookies.append(cookie)

    if not cookies:
        raise RuntimeError(
            f"No cookies found for {domain} in Brave browser.\n"
            "Open Brave, go to https://sattacademy.com and log in first."
        )

    # Check for essential cookies
    cookie_names = {c["name"] for c in cookies}
    essential = {"XSRF-TOKEN", "satt_academy_session"}
    missing = essential - cookie_names
    if missing:
        print(f"[COOKIES] WARNING: Missing essential cookies: {missing}")
        print("[COOKIES] You may need to log in to sattacademy.com in Brave first.")
    else:
        print(f"[COOKIES] Extracted {len(cookies)} cookies (session cookies found)")

    return cookies


def get_browser_config(headless: bool = True) -> BrowserConfig:
    """
    Get BrowserConfig with Brave cookies injected for authenticated scraping.
    """
    cookies = extract_brave_cookies()

    return BrowserConfig(
        browser_type="chromium",
        headless=headless,
        cookies=cookies,
        verbose=False,
        extra_args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
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
    """Verify extracted cookies can access authenticated Satt Academy pages."""
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
                    print("[VERIFY] Log in to sattacademy.com in Brave, then try again.")
                    return False

            print("[VERIFY] Could not verify. Page may have loaded but data not found.")
            return False
    except Exception as e:
        print(f"[VERIFY] Error: {e}")
        return False
