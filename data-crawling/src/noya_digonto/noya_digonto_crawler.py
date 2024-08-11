import sys
import os
from datetime import datetime
import logging
import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from news_crawler import NewsCrawler
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get today's date to fetch todays all news
TODAY_DATE = datetime.now().strftime('%Y-%m-%d')
ARCHEIVE_URL = f'https://www.dailynayadiganta.com/archive/{TODAY_DATE}'
BASE_URL = 'https://www.dailynayadiganta.com/'

class NoyaDigontoCrawler(NewsCrawler):
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

    def get_article_urls(self, archeive_url):
        logging.info(f"Fetching article URLs from archive: {archeive_url}")
        soup = self.fetch_page(archeive_url)
        if soup:
            links = soup.select('.archive-news-list a')
            article_urls = [link.get('href') for link in links]
            logging.info(f"Found {len(article_urls)} article URLs")
            return article_urls
        logging.warning(f"No article URLs found for archive: {archeive_url}")
        return []
    
    def parse_article(self, article_url):
        logging.info(f"Parsing article: {article_url}")
        soup = self.fetch_page(article_url)
        if soup:
            headline = soup.select_one('.headline').text if soup.select_one('.headline') else ''
            publication_date = soup.select_one('.article-info ul li').find_next('li').text if soup.select_one('.article-info ul li') else ''
            article_descriptions = ' '.join([desc.text for desc in soup.select('.news-content')])
            suggested_article_titles = [title.text for title in soup.select('strong')]
            suggested_article_links = [link.get('href') for link in soup.select('.news-title h3 a')]
            category = [cat.text for cat in soup.select('.breadcrumb li a')]
            
            suggested_articles = []
            for title, link in zip(suggested_article_titles, suggested_article_links):
                suggested_articles.append({
                    'title': title,
                    'link': link
                })

            article_data = {
                'headline': headline,
                'publication_date': publication_date,
                'article_descriptions': article_descriptions,
                'suggested_articles': suggested_articles,
                'suggested_article_links': suggested_article_links,
                'category': category,
                'crawl_date': datetime.now().isoformat()
            }
            logging.info(f"Successfully parsed article: {article_url}")
            return article_data
        logging.warning(f"Failed to parse article: {article_url}")
        return {}
    
    def parse_all_articles(self, archive_url):
        logging.info(f"Starting to parse all articles from archive: {archive_url}")
        article_urls = self.get_article_urls(archive_url)
        all_articles = []
        for url in article_urls:
            article_data = self.parse_article(url)
            if article_data:
                all_articles.append(article_data)
        logging.info(f"Finished parsing all articles from archive: {archive_url}")
        return all_articles

    def crawl(self):
        article_urls = self.get_article_urls(ARCHEIVE_URL)
        for article_url in article_urls:
            article_data = self.parse_article(article_url)
            if article_data:
                self.save_to_elasticsearch(article_data)

if __name__ == '__main__':
    crawler = NoyaDigontoCrawler()
    crawler.crawl()