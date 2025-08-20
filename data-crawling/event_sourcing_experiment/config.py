from pathlib import Path

class ScraperConfig:
    """Simple configuration for the news scraper"""
    
    # File paths
    CSV_FILE_PATH = "bangladesh_news_events.csv"
    OUTPUT_DIRECTORY = "scraped_news"
    
    # Browser settings
    HEADLESS_MODE = False  # Set to True to hide browser
    BROWSER_TIMEOUT = 30000  # 20 seconds
    
    # Scraping settings
    MAX_PAGES_PER_EVENT = 50  # Maximum Google search pages per event (increased from 3)
    MAX_EVENTS_TO_PROCESS = 100  # Process only first 2 events for testing
    START_FROM_EVENT_INDEX = 0
    
    # Delays (seconds) - be respectful to Google
    DELAY_BETWEEN_PAGES = 3
    DELAY_BETWEEN_EVENTS = 2
    DELAY_BETWEEN_URLS = 1
    
    # Proxy settings (optional)
    USE_PROXY = False
    PROXY = None  # Set to {"server": "http://proxy:port"} if needed
    
    @classmethod
    def validate_config(cls):
        """Validate configuration"""
        if not Path(cls.CSV_FILE_PATH).exists():
            raise ValueError(f"CSV file not found: {cls.CSV_FILE_PATH}")
        return True
