# import asyncio
# import logging
# from config import ScraperConfig
# from complete_news_scraper import SimpleGoogleScraper

# def setup_logging():
#     """Setup logging configuration"""
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#         handlers=[
#             logging.FileHandler('scraper.log'),
#             logging.StreamHandler()
#         ]
#     )

# async def run_scraper_with_config():
#     """Run the scraper with configuration settings"""
    
#     # Validate configuration
#     try:
#         ScraperConfig.validate_config()
#         logging.info("✅ Configuration validated successfully")
#     except ValueError as e:
#         logging.error(f"❌ Configuration error: {e}")
#         return
    
#     # Create scraper instance
#     scraper = SimpleGoogleScraper(
#         csv_file_path=ScraperConfig.CSV_FILE_PATH,
#         output_dir=ScraperConfig.OUTPUT_DIRECTORY,
#         headless=False,
#         proxy=ScraperConfig.get_proxy()
#     )
    
#     # Override internal settings with config
#     scraper.max_pages = ScraperConfig.MAX_PAGES_PER_EVENT
    
#     logging.info(f"🚀 Starting Bangladesh News Event Scraper")
#     logging.info(f"📁 CSV File: {ScraperConfig.CSV_FILE_PATH}")
#     logging.info(f"📂 Output Directory: {ScraperConfig.OUTPUT_DIRECTORY}")
#     logging.info(f"🖥️ Headless Mode: {ScraperConfig.HEADLESS_MODE}")
#     logging.info(f"🔄 Max Pages per Event: {ScraperConfig.MAX_PAGES_PER_EVENT}")
    
#     # Start scraping
#     await scraper.scrape_all_events(
#         start_index=ScraperConfig.START_FROM_EVENT_INDEX,
#         max_events=ScraperConfig.MAX_EVENTS_TO_PROCESS
#     )

# if __name__ == "__main__":
#     setup_logging()
#     asyncio.run(run_scraper_with_config())

import asyncio
import logging
from config import ScraperConfig
from complete_news_scraper import SimpleBangladeshNewsScraper

def setup_logging():
    """Setup simple logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper.log'),
            logging.StreamHandler()
        ]
    )

async def run_simple_scraper():
    """Run the simplified scraper"""
    
    # Validate config
    try:
        ScraperConfig.validate_config()
        logging.info("✅ Configuration validated")
    except ValueError as e:
        logging.error(f"❌ Configuration error: {e}")
        return
    
    # Create scraper
    scraper = SimpleBangladeshNewsScraper(
        csv_file_path=ScraperConfig.CSV_FILE_PATH,
        output_dir=ScraperConfig.OUTPUT_DIRECTORY,
        headless=ScraperConfig.HEADLESS_MODE,
        proxy=ScraperConfig.PROXY
    )
    
    # Set max pages
    scraper.max_pages_per_event = ScraperConfig.MAX_PAGES_PER_EVENT
    
    logging.info(f"🚀 Starting Simple News Scraper")
    logging.info(f"📁 CSV File: {ScraperConfig.CSV_FILE_PATH}")
    logging.info(f"📂 Output: {ScraperConfig.OUTPUT_DIRECTORY}")
    logging.info(f"🖥️ Headless: {ScraperConfig.HEADLESS_MODE}")
    logging.info(f"📄 Max Pages: {ScraperConfig.MAX_PAGES_PER_EVENT}")
    logging.info(f"📊 Max Events: {ScraperConfig.MAX_EVENTS_TO_PROCESS}")
    
    # Start scraping
    await scraper.scrape_all_events(
        start_index=ScraperConfig.START_FROM_EVENT_INDEX,
        max_events=ScraperConfig.MAX_EVENTS_TO_PROCESS
    )

if __name__ == "__main__":
    setup_logging()
    asyncio.run(run_simple_scraper())