import sys
import os
from datetime import datetime, timedelta
import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_crawler import NewsCrawler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProthomAloCrawler(NewsCrawler):
    def __init__(self, es_host='localhost', es_port=9200):
        super().__init__('https://www.prothomalo.com', es_host, es_port)
        self.setup_selenium()

    def setup_selenium(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)

    def get_article_urls(self, date):
        # Convert date to timestamp (milliseconds)
        date_timestamp = int(date.timestamp() * 1000)
        next_day_timestamp = int((date + timedelta(days=1)).timestamp() * 1000)
        
        search_url = f'{self.base_url}/search?published-before={next_day_timestamp}&published-after={date_timestamp}'
        self.driver.get(search_url)
        time.sleep(15)  # Wait for page to load

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        links = soup.select('.archive-news a')
        return [link.get('href') for link in links]

    def parse_article(self, article_url):
        soup = self.fetch_page(article_url)
        if soup is None:
            logging.error(f"Failed to fetch article page: {article_url}")
            return None

        try:
            headline = soup.find('h1')
            headline_text = headline.text.strip() if headline else ''

            finding_date = soup.select('.post-text p')
            publication_date = finding_date[1].text.strip() if len(finding_date) > 1 else ''

            article_description = soup.select_one('article')
            content = article_description.text.strip() if article_description else ''

            topics = [topic.text.strip() for topic in soup.select('.tag-ul li a')]

            suggested_articles = []
            for title, link in zip(soup.select('.more-news-single .more-news-single-text h3'), 
                                   soup.select('.more-news-single a')):
                suggested_articles.append({
                    'title': title.text.strip(),
                    'link': link.get('href')
                })

            article = {
                'url': article_url,
                'headline': headline_text,
                'content': content,
                'publication_date': publication_date,
                'topics': topics,
                'suggested_articles': suggested_articles,
                'crawl_date': datetime.now().isoformat()
            }

            return article
        except Exception as e:
            logging.error(f"Error parsing article {article_url}: {e}")
            return None

    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
        super().__del__()

def main():
    crawler = ProthomAloCrawler()
    today = datetime.now().date()
    articles = crawler.get_all_articles_of_date(today)
    logging.info(f"Crawled {len(articles)} articles from Prothom Alo for {today}")

    if not crawler.es_available:
        logging.warning("Elasticsearch is not available. Articles were not saved to the database.")
        logging.info("To save articles, ensure Elasticsearch is running and modify the code to connect.")

    # Optionally, you can process or save the articles in a different way here
    # For example, you could save them to a file:
    # with open(f'prothom_alo_articles_{today}.txt', 'w', encoding='utf-8') as f:
    #     for article in articles:
    #         f.write(f"Headline: {article['headline']}\n")
    #         f.write(f"URL: {article['url']}\n")
    #         f.write(f"Content: {article['content'][:500]}...\n\n")

if __name__ == "__main__":
    main()