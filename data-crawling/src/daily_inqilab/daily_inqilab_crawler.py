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
        super().__init__(BASE_URL, es_host, es_port)
        logging.info("DailyInqilabCrawler initialized with ES host: %s, port: %d", es_host, es_port)

    def fetch_page(self, url):
        logging.info("Fetching page: %s", url)
        try:
            self.driver.get(url)
            self.driver.implicitly_wait(10)
            source = self.driver.page_source
            self.init_beautifulsoup(source)
            logging.info("Page fetched successfully: %s", url)
            return self.soup
        except requests.RequestException as e:
            logging.error(f"Error fetching page {url}: {e}")
            return None

    def get_pagination_info(self, soup):
        pagination = soup.select('.single-archive-item .pagination a')
        if len(pagination) >= 3:
            third_last_link = pagination[-3]
            href = third_last_link.get('href')
            parsed_url = urlparse(href)
            page_number = parse_qs(parsed_url.query).get('page', [None])[0]
            return int(page_number)
        return 0

    def get_article_urls_from_page(self, soup):
        articles_urls = soup.select('h3 a')
        return [article.get('href') for article in articles_urls]

    def get_article_urls(self):
        logging.info("Getting article URLs from archive: %s", ARCHIVE_URL)
        soup = self.fetch_page(url=ARCHIVE_URL)
        number_of_pages = self.get_pagination_info(soup)
        logging.info("Total number of pages to crawl: %d", number_of_pages)
        
        all_articles_urls = []
        for page_number in range(1, number_of_pages + 1):
            url = f'{ARCHIVE_URL}&page={page_number}'
            logging.info("Fetching articles from page: %d", page_number)
            soup = self.fetch_page(url)
            all_articles_urls.extend(self.get_article_urls_from_page(soup))
        
        logging.info("Total articles found: %d", len(all_articles_urls))
        return all_articles_urls

    def parse_article_content(self, soup):
        article_descriptions = soup.select('.new-details .description p')
        descriptions = ' '.join([desc.text for desc in article_descriptions])
        return descriptions

    def parse_suggested_links(self, soup):
        exclude_urls = [
            'https://dailyinqilab.com',
            'https://dailyinqilab.com/national',
            'javascript:void(0)',
            'http://www.htmlcommentbox.com'
        ]
        links = [link.get('href') for link in soup.select('.mt-3 a') if link.get('href') not in exclude_urls]
        return links

    def parse_suggested_titles(self, soup):
        exclude_titles = [
            'জাতীয়',
            'অনলাইন ডেস্ক',
            'HTML Comment Box',
            'আরও',
            "মহানগর",
            ""
        ]
        titles = [title.text.strip() for title in soup.select('.mt-3 a') if title.text.strip() not in exclude_titles]
        return titles

    def parse_article(self, article_url):
        logging.info("Parsing article: %s", article_url)
        soup = self.fetch_page(article_url)
        headline = soup.select_one('.col-md-9 h2').text if soup.select_one('.col-md-9 h2') else ""
        article_content = self.parse_article_content(soup) if soup.select('.new-details .description p') else ""    
        publication_date = soup.select_one('.news-date-time').text if soup.select_one('.news-date-time') else ""
        category = soup.select_one('.col-md-9 p a').text if soup.select_one('.col-md-9 p a') else ""
        suggested_article_links = self.parse_suggested_links(soup) if soup.select('.mt-3 a') else ""
        suggested_article_titles = self.parse_suggested_titles(soup) if soup.select('.mt-3 a') else ""
        
        logging.info("Article parsed successfully: %s", article_url)
        return {
            "headline": headline,
            "content": article_content,
            "publication_date": publication_date,
            "category": category,
            "suggested_article_links": suggested_article_links,
            "suggested_article_titles": suggested_article_titles
        }

    def crawl(self):
        logging.info("Starting crawling process")
        all_urls = self.get_article_urls()
        for article_url in all_urls:
            article_data = self.parse_article(article_url)
            logging.info("Article data fetched successfully")
            self.save_to_elasticsearch(article_data)

if __name__ == "__main__":
    crawler = DailyInqilabCrawler()
    crawler.crawl()