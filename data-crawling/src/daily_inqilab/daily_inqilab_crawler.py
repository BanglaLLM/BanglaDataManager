import sys
import os
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_crawler import NewsCrawler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


TODAY_DATE = datetime.now().strftime('%Y-%m-%d')
BASE_URL = 'https://dailyinqilab.com/'
ARCHIVE_URL = f'{BASE_URL}archive?cat=&dateFrom={TODAY_DATE}&dateTo={TODAY_DATE}'





class DailyInqilabCrawler(NewsCrawler):
    def __init__(self, es_host='localhost', es_port=9200):
        super().__init__(BASE_URL, es_host, es_port) # Initialize the Selenium WebDriver
        logging.info("DailyInqilabCrawler initialized with ES host: %s, port: %d", es_host, es_port)

    def fetch_page(self, url):
        logging.info("Fetching article URLs for date: %s", url)
        try:
            self.driver.get(url)
            self.driver.implicitly_wait(10)
            source = self.driver.page_source
            self.init_beautifulsoup(source)
            return self.soup
        except requests.RequestException as e:
            logging.error(f"Error fetching page {url}: {e}")
            return None
    
    def get_article_urls(self):
        soup = self.fetch_page(url=ARCHIVE_URL)
        print(soup.prettify())
        pagination = soup.select('.single-archive-item .pagination a')
        # print(pagination) 
        if len(pagination) >= 3:
            third_last_link = pagination[-3] # getting the third last link which contains the information that how many page we have to crawl
            # print(third_last_link) # https://dailyinqilab.com/archive?dateFrom=2024-08-10&amp;dateTo=2024-08-10&amp;page=2
            href = third_last_link.get('href')
            parsed_url = urlparse(href)
            page_number = parse_qs(parsed_url.query).get('page', [None])[0]
            number_of_pages = int(page_number)
            COUNT_PAGE_NUMBER = 1
            all_articles_urls = []
            while COUNT_PAGE_NUMBER <= number_of_pages:
                url = f'{ARCHIVE_URL}&page={COUNT_PAGE_NUMBER}'
                print(url)
                soup = self.fetch_page(url)
                articles_urls  = soup.select('h3 a')
                # print(articles_urls)
                for article in articles_urls:
                    article_url = article.get('href')
                    all_articles_urls.append(article_url)
                COUNT_PAGE_NUMBER += 1
            return all_articles_urls
            
    def parse_article(self, article_url):
        pass



init = DailyInqilabCrawler()
init.get_article_urls()

