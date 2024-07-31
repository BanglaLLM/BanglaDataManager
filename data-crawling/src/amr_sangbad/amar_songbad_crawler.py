import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from news_crawler import NewsCrawler
from datetime import datetime
import logging
import requests

# Get today's date to fetch today's article
TODAYS_DATE = datetime.now().strftime('%d/%m/%Y')
ARCHIVE_URL = f'https://www.amarsangbad.com/archive?txtDate={TODAYS_DATE}' 
BASE_URL = 'https://www.amarsangbad.com/'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AmarSangbandCrawler(NewsCrawler):
    def __init__(self, es_host='localhost', es_port=9200):
        super().__init__(BASE_URL, es_host, es_port)
    
    def fetch_page(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.init_beautifulsoup(response.text)
            return self.soup
        except requests.RequestException as e:
            logging.error(f"Error fetching page {url}: {e}")
            return None
    
    def get_article_urls(self, archive_url):
        logging.info(f"Fetching article URLs from archive: {archive_url}")
        try:
            soup = self.fetch_page(archive_url)
            if soup:
                links = soup.select('.archive-news a')
                article_urls = [link.get('href') for link in links]
                logging.info(f"Found {len(article_urls)} article URLs")
                return article_urls
            logging.warning(f"No article URLs found for archive: {archive_url}")
        except Exception as e:
            logging.error(f"Error getting article URLs from {archive_url}: {e}")
        return []
    
    def parse_article(self, article_url):
        logging.info(f"Parsing article: {article_url}")
        try:
            soup = self.fetch_page(article_url)
            if soup:
                article_data = {
                    'headline': soup.find('h1').text if soup.find('h1') else '',
                    'publication_date': soup.select('.post-text p')[1].text if len(soup.select('.post-text p')) > 1 else '',
                    'article_description': soup.select_one('article').text if soup.select_one('article') else '',
                    'topics': [topic.text for topic in soup.select('.tag-ul li a')],
                    'suggested_article_titles': [title.text for title in soup.select('.more-news-single .more-news-single-text h3')],
                    'suggested_article_links': [link.get('href') for link in soup.select('.more-news-single a')]
                }
                logging.info(f"Successfully parsed article: {article_url}")
                return article_data
            logging.warning(f"Failed to parse article: {article_url}")
        except Exception as e:
            logging.error(f"Error parsing article {article_url}: {e}")
        return {}
    
    def parse_all_articles(self, archive_url):
        logging.info(f"Starting to parse all articles from archive: {archive_url}")
        try:
            article_urls = self.get_article_urls(archive_url)
            all_articles = []
            for url in article_urls:
                article_data = self.parse_article(url)
                if article_data:
                    all_articles.append(article_data)
            logging.info(f"Finished parsing all articles from archive: {archive_url}")
            return all_articles
        except Exception as e:
            logging.error(f"Error parsing all articles from {archive_url}: {e}")
        return []
    
    def crawl(self):
        try:
            article_urls = self.get_article_urls(ARCHIVE_URL)
            for article_url in article_urls:
                article_data = self.parse_article(article_url)
                if article_data:
                    self.save_to_elasticsearch(article_data)
        except Exception as e:
            logging.error(f"Error during crawling: {e}")
    
if __name__ == '__main__':
    try:
        crawler = AmarSangbandCrawler()
        crawler.crawl()
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
