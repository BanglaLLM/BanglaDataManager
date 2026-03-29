"""
Satt Academy Admission Question Scraper (crawl4ai-based).

Scrapes admission exam MCQ and written questions from sattacademy.com
using a persistent browser profile for authenticated access past Cloudflare
and Google OAuth.

Usage:
    # Verify cookies work
    python -m tutorlm_data_scraping.satt_academy --verify

    # Scrape questions
    python -m tutorlm_data_scraping.satt_academy --university dhaka-university

    # Resume after interruption (skips already-scraped exams)
    python -m tutorlm_data_scraping.satt_academy --university dhaka-university

    # Start fresh
    python -m tutorlm_data_scraping.satt_academy --university dhaka-university --fresh
"""

import asyncio
import json
import os
import random
import argparse
import logging
import sys
from datetime import datetime

from crawl4ai import AsyncWebCrawler

from .config import (
    BASE_URL,
    DEFAULT_UNIVERSITY_SLUG,
    UNIVERSITY_CATEGORIES,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    BACKOFF_BASE,
    BACKOFF_MAX,
    MAX_RETRIES,
    COOLDOWN_AFTER_ERRORS,
    COOLDOWN_BETWEEN_UNIS,
    OUTPUT_DIR,
)
from .session_manager import (
    get_browser_config,
    get_crawl_config,
    verify_session,
)
from .parsers import parse_category_page, parse_mcq_questions, parse_written_questions

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logger = logging.getLogger("satt_scraper")


def setup_logging(output_dir: str):
    """Configure logging to both console and file."""
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(message)s", datefmt="%H:%M:%S"
    )

    # Console handler - INFO level
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler - DEBUG level (detailed)
    os.makedirs(output_dir, exist_ok=True)
    log_file = os.path.join(output_dir, f"scraper_{datetime.now():%Y%m%d_%H%M%S}.log")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.info(f"Log file: {log_file}")


# Per-request timeout (seconds). If a single crawl4ai fetch exceeds this, we abort it.
FETCH_TIMEOUT = 45



# Single combined output filename for all universities
OUTPUT_FILENAME = "satt_academy_admission_questions.jsonl"


class SattAdmissionScraper:
    """Scrapes admission questions from Satt Academy using crawl4ai."""

    def __init__(self, university_slug: str = DEFAULT_UNIVERSITY_SLUG, output_dir: str = None):
        self.university_slug = university_slug
        self.category_id = UNIVERSITY_CATEGORIES.get(university_slug)
        if not self.category_id:
            raise ValueError(
                f"Unknown university: {university_slug}. "
                f"Available: {list(UNIVERSITY_CATEGORIES.keys())}"
            )

        self.output_dir = output_dir or OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        setup_logging(self.output_dir)

        self.browser_config = get_browser_config(headless=True)
        self.crawl_config = get_crawl_config()
        self.crawler = None
        self._consecutive_errors = 0

        # Resume support — per-university progress file
        self._progress_file = os.path.join(self.output_dir, f"{university_slug}_progress.json")
        self._completed_exams = self._load_progress()

    def _load_progress(self) -> set:
        if os.path.exists(self._progress_file):
            with open(self._progress_file, "r") as f:
                data = json.load(f)
                completed = set(data.get("completed_exams", []))
                logger.debug(f"Loaded progress: {len(completed)} exams already completed")
                return completed
        return set()

    def _save_progress(self, subcat_id: str):
        self._completed_exams.add(subcat_id)
        with open(self._progress_file, "w") as f:
            json.dump({"completed_exams": list(self._completed_exams)}, f)

    def _save_questions(self, questions: list, exam_info: dict):
        output_file = os.path.join(self.output_dir, OUTPUT_FILENAME)
        with open(output_file, "a", encoding="utf-8") as f:
            for q in questions:
                record = {
                    "university": self.university_slug,
                    "exam_name": exam_info.get("name", ""),
                    "exam_year": exam_info.get("year", ""),
                    "subcat_id": exam_info.get("subcat_id", ""),
                    **q,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    async def _random_delay(self):
        """Sleep a random duration between requests to avoid rate limiting."""
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        logger.debug(f"    Sleeping {delay:.1f}s...")
        await asyncio.sleep(delay)

    async def _fetch_html(self, url: str, label: str = "") -> str | None:
        """Fetch a page's HTML with retry logic, per-request timeout, and exponential backoff."""
        short_url = url.split("?")[0][-60:]  # last 60 chars of path for logging
        tag = f"[{label}]" if label else ""

        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"{tag} Fetching (attempt {attempt+1}): {url}")

                # Wrap in asyncio.wait_for to enforce a hard timeout
                result = await asyncio.wait_for(
                    self.crawler.arun(url=url, config=self.crawl_config),
                    timeout=FETCH_TIMEOUT,
                )

                if result.success:
                    html = result.html or ""
                    redirected = result.redirected_url or result.url or ""
                    logger.debug(
                        f"{tag} Fetched OK: {len(html)} bytes, "
                        f"redirected={redirected[:80] if redirected != url else 'no'}"
                    )

                    if "/login" in redirected:
                        logger.warning(f"{tag} Redirected to login! Session expired.")
                        return None

                    # Reset consecutive error counter on success
                    self._consecutive_errors = 0
                    return html
                else:
                    err_msg = result.error_message or "unknown"
                    logger.warning(
                        f"{tag} Fetch failed (attempt {attempt+1}): "
                        f"{err_msg[:200]} | url={short_url}"
                    )

            except asyncio.TimeoutError:
                logger.warning(
                    f"{tag} TIMEOUT after {FETCH_TIMEOUT}s (attempt {attempt+1}) | url={short_url}"
                )
            except Exception as e:
                logger.error(
                    f"{tag} Exception (attempt {attempt+1}): {type(e).__name__}: {e} | url={short_url}"
                )

            # Exponential backoff: 30s, 60s, 120s (capped at BACKOFF_MAX)
            self._consecutive_errors += 1
            backoff = min(BACKOFF_BASE * (2 ** attempt), BACKOFF_MAX)
            # Add jitter
            backoff = backoff + random.uniform(0, backoff * 0.3)
            logger.info(f"{tag} Backing off {backoff:.0f}s before retry (consecutive_errors={self._consecutive_errors})...")
            await asyncio.sleep(backoff)

        logger.error(f"{tag} GAVE UP after {MAX_RETRIES} attempts: {short_url}")

        # If we've had many consecutive errors, do a longer cooldown
        if self._consecutive_errors >= 3:
            logger.warning(
                f"    !! {self._consecutive_errors} consecutive errors. "
                f"Cooling down for {COOLDOWN_AFTER_ERRORS}s to let server recover..."
            )
            await asyncio.sleep(COOLDOWN_AFTER_ERRORS)

        return None

    # -------------------------------------------------------------------------
    # Step 1: Scrape category page to get all exam listings
    # -------------------------------------------------------------------------
    async def scrape_exam_listings(self) -> list:
        logger.info(f"{'='*60}")
        logger.info(f"Scraping exam listings for: {self.university_slug}")
        logger.info(f"{'='*60}")

        all_exams = []
        page = 1

        while True:
            url = (
                f"{BASE_URL}/admission/category/{self.university_slug}"
                f"?categories%5B%5D={self.category_id}"
                f"&request_data_type=job&page={page}"
            )
            logger.info(f"  [LISTING PAGE {page}] Fetching...")

            html = await self._fetch_html(url, label=f"listing-p{page}")
            if not html:
                logger.warning(f"  [LISTING PAGE {page}] No HTML returned, stopping.")
                break

            result = parse_category_page(html)
            exams = result["exams"]

            if not exams:
                logger.info(f"  [LISTING PAGE {page}] No exams found, done.")
                break

            all_exams.extend(exams)
            logger.info(f"  [LISTING PAGE {page}] Found {len(exams)} exams (total: {len(all_exams)})")

            if not result["has_next_page"]:
                logger.debug(f"  [LISTING PAGE {page}] No next page link.")
                break

            page += 1
            await self._random_delay()

        logger.info(f"Total exams found: {len(all_exams)}")

        # Save exam listing
        listing_file = os.path.join(self.output_dir, f"{self.university_slug}_exams.json")
        with open(listing_file, "w", encoding="utf-8") as f:
            json.dump(all_exams, f, ensure_ascii=False, indent=2)
        logger.info(f"Exam listing saved to: {listing_file}")

        return all_exams

    # -------------------------------------------------------------------------
    # Step 2: Scrape MCQ questions for a single exam
    # -------------------------------------------------------------------------
    async def scrape_mcq_questions(self, exam: dict) -> list:
        mcq_url = exam["mcq_url"]
        subcat = exam["subcat_id"]
        questions = []
        page = 1

        while True:
            url = f"{mcq_url}?page={page}&mode=reading"
            logger.info(f"      [MCQ p{page}] Fetching subcat={subcat}...")

            html = await self._fetch_html(url, label=f"mcq-{subcat}-p{page}")
            if not html:
                logger.warning(f"      [MCQ p{page}] No HTML, stopping MCQ scrape.")
                break

            result = parse_mcq_questions(html)

            if result.get("is_empty"):
                logger.debug(f"      [MCQ p{page}] Empty page (end of questions).")
                break

            if not result["questions"]:
                logger.debug(f"      [MCQ p{page}] No questions parsed from HTML.")
                break

            questions.extend(result["questions"])
            logger.info(
                f"      [MCQ p{page}] Parsed {len(result['questions'])} questions "
                f"(subject: {result.get('subject', '?')}, running total: {len(questions)})"
            )

            if not result["has_next_page"]:
                logger.debug(f"      [MCQ p{page}] No next page.")
                break

            page += 1
            await self._random_delay()

        return questions

    # -------------------------------------------------------------------------
    # Step 3: Scrape written questions for a single exam
    # -------------------------------------------------------------------------
    async def scrape_written_questions(self, exam: dict) -> list:
        written_url = exam["written_url"]
        subcat = exam["subcat_id"]
        questions = []
        page = 1

        while True:
            url = f"{written_url}?page={page}&mode=reading"
            logger.info(f"      [WRITTEN p{page}] Fetching subcat={subcat}...")

            html = await self._fetch_html(url, label=f"written-{subcat}-p{page}")
            if not html:
                logger.debug(f"      [WRITTEN p{page}] No HTML (may not exist), stopping.")
                break

            result = parse_written_questions(html)

            if result.get("is_empty"):
                logger.debug(f"      [WRITTEN p{page}] Empty page.")
                break

            if not result["questions"]:
                logger.debug(f"      [WRITTEN p{page}] No questions parsed.")
                break

            questions.extend(result["questions"])
            logger.info(
                f"      [WRITTEN p{page}] Parsed {len(result['questions'])} questions "
                f"(running total: {len(questions)})"
            )

            if not result["has_next_page"]:
                break

            page += 1
            await self._random_delay()

        return questions

    # -------------------------------------------------------------------------
    # Main orchestrator
    # -------------------------------------------------------------------------
    async def run(self):
        logger.info(f"Starting scraper at {datetime.now():%Y-%m-%d %H:%M:%S}")

        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            self.crawler = crawler
            logger.info("Browser launched successfully.")

            # Step 1: Get all exam listings
            exams = await self.scrape_exam_listings()

            if not exams:
                logger.error("No exams found. Check session or university slug.")
                return

            # Filter already completed exams
            remaining = [e for e in exams if e["subcat_id"] not in self._completed_exams]
            if len(remaining) < len(exams):
                logger.info(
                    f"Resuming: {len(exams) - len(remaining)} done, "
                    f"{len(remaining)} remaining"
                )

            total_mcq = 0
            total_written = 0

            logger.info(f"{'='*60}")
            logger.info(f"Scraping questions for {len(remaining)} exams")
            logger.info(f"{'='*60}")

            for i, exam in enumerate(remaining):
                subcat_id = exam["subcat_id"]

                logger.info(
                    f"\n[{i+1}/{len(remaining)}] {exam['name']}"
                )
                logger.info(
                    f"    subcat_id={subcat_id}  expected_q=~{exam['total_questions']}  "
                    f"types={exam.get('question_types', ['mcq'])}"
                )

                # Scrape MCQ questions
                mcq_questions = []
                if "mcq" in exam.get("question_types", ["mcq"]):
                    logger.info("    >> Scraping MCQ...")
                    mcq_questions = await self.scrape_mcq_questions(exam)
                    logger.info(f"    >> MCQ done: {len(mcq_questions)} questions")
                    total_mcq += len(mcq_questions)

                # Scrape written questions
                written_questions = []
                logger.info("    >> Checking written questions...")
                written_questions = await self.scrape_written_questions(exam)
                if written_questions:
                    logger.info(f"    >> Written done: {len(written_questions)} questions")
                    total_written += len(written_questions)
                else:
                    logger.info("    >> No written questions found")

                # Save
                all_exam_questions = mcq_questions + written_questions
                if all_exam_questions:
                    self._save_questions(all_exam_questions, exam)
                    logger.info(
                        f"    >> Saved {len(all_exam_questions)} questions to JSONL"
                    )

                self._save_progress(subcat_id)
                logger.info(
                    f"    >> Progress saved. Running totals: MCQ={total_mcq} Written={total_written}"
                )
                await self._random_delay()

            # Summary
            logger.info(f"\n{'='*60}")
            logger.info(f"SCRAPING COMPLETE at {datetime.now():%Y-%m-%d %H:%M:%S}")
            logger.info(f"{'='*60}")
            logger.info(f"University: {self.university_slug}")
            logger.info(f"Exams scraped: {len(remaining)}")
            logger.info(f"MCQ questions: {total_mcq}")
            logger.info(f"Written questions: {total_written}")
            output_file = os.path.join(self.output_dir, OUTPUT_FILENAME)
            logger.info(f"Output: {output_file}")
            logger.info(f"{'='*60}")


async def run_all_universities(output_dir: str = None, fresh: bool = False):
    """Scrape all universities sequentially, sharing a single browser session."""
    out = output_dir or OUTPUT_DIR
    os.makedirs(out, exist_ok=True)
    setup_logging(out)

    if fresh:
        # Clear combined JSONL
        combined = os.path.join(out, OUTPUT_FILENAME)
        if os.path.exists(combined):
            os.remove(combined)
            logger.info(f"Cleared old combined output: {combined}")
        # Clear all per-university progress files
        for slug in UNIVERSITY_CATEGORIES:
            pf = os.path.join(out, f"{slug}_progress.json")
            if os.path.exists(pf):
                os.remove(pf)
        logger.info("Cleared all progress files.")

    slugs = list(UNIVERSITY_CATEGORIES.keys())
    grand_mcq = 0
    grand_written = 0
    grand_exams = 0

    logger.info(f"{'='*60}")
    logger.info(f"SCRAPING ALL {len(slugs)} UNIVERSITIES")
    logger.info(f"{'='*60}")

    for idx, slug in enumerate(slugs):
        logger.info(f"\n{'#'*60}")
        logger.info(f"# [{idx+1}/{len(slugs)}] UNIVERSITY: {slug}")
        logger.info(f"{'#'*60}")

        try:
            scraper = SattAdmissionScraper(
                university_slug=slug,
                output_dir=output_dir,
            )
            await scraper.run()

            # Tally (read back from progress)
            pf = os.path.join(out, f"{slug}_progress.json")
            if os.path.exists(pf):
                with open(pf) as f:
                    data = json.load(f)
                    grand_exams += len(data.get("completed_exams", []))

        except Exception as e:
            logger.error(f"Failed on {slug}: {type(e).__name__}: {e}")
            logger.info("Continuing to next university...")

        # Cooldown between universities
        if idx < len(slugs) - 1:
            logger.info(f"Cooling down {COOLDOWN_BETWEEN_UNIS}s before next university...")
            await asyncio.sleep(COOLDOWN_BETWEEN_UNIS)

    # Count total lines in combined output
    combined = os.path.join(out, OUTPUT_FILENAME)
    total_lines = 0
    if os.path.exists(combined):
        with open(combined) as f:
            total_lines = sum(1 for _ in f)

    logger.info(f"\n{'='*60}")
    logger.info(f"ALL UNIVERSITIES COMPLETE at {datetime.now():%Y-%m-%d %H:%M:%S}")
    logger.info(f"{'='*60}")
    logger.info(f"Universities attempted: {len(slugs)}")
    logger.info(f"Total questions in output: {total_lines}")
    logger.info(f"Output: {combined}")
    logger.info(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape admission questions from Satt Academy"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--university",
        type=str,
        choices=list(UNIVERSITY_CATEGORIES.keys()),
        help="Scrape a single university",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Scrape ALL universities (37 total)",
    )
    group.add_argument(
        "--verify",
        action="store_true",
        help="Verify saved session is still valid",
    )
    group.add_argument(
        "--list",
        action="store_true",
        dest="list_unis",
        help="List all available university slugs",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for scraped data",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Start fresh (ignore previous progress, clear old output)",
    )

    args = parser.parse_args()

    # List mode
    if args.list_unis:
        print(f"Available universities ({len(UNIVERSITY_CATEGORIES)}):\n")
        for slug, cat_id in UNIVERSITY_CATEGORIES.items():
            print(f"  {slug}  (category_id={cat_id})")
        return

    # Verify mode
    if args.verify:
        asyncio.run(verify_session())
        return

    # All universities mode
    if args.all:
        asyncio.run(run_all_universities(output_dir=args.output_dir, fresh=args.fresh))
        return

    # Single university mode (default to dhaka-university)
    slug = args.university or DEFAULT_UNIVERSITY_SLUG

    scraper = SattAdmissionScraper(
        university_slug=slug,
        output_dir=args.output_dir,
    )

    if args.fresh:
        if os.path.exists(scraper._progress_file):
            os.remove(scraper._progress_file)
            scraper._completed_exams = set()
            logger.info("Cleared previous progress.")
        combined = os.path.join(scraper.output_dir, OUTPUT_FILENAME)
        if os.path.exists(combined):
            os.remove(combined)
            logger.info("Cleared old output.")

    asyncio.run(scraper.run())


if __name__ == "__main__":
    main()
