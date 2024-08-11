from datetime import datetime
import logging
import os
import sys
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
from bs4 import BeautifulSoup
#Added parent directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from news_crawler import NewsCrawler

# Get today's date to fetch today's all article
TODAYS_DATE = datetime.now().strftime('%Y-%m-%d')
BASE_URL = 'https://www.ittefaq.com.bd/'
ARCHIVE_URL = f'https://www.ittefaq.com.bd/archive/{TODAYS_DATE}'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class IttefaqCrawler(NewsCrawler):
    def __init__(self, es_host='localhost', es_port=9200):
        super().__init__(BASE_URL, es_host, es_port)
        
    def load_all_article(self):
        logging.info(f'Loading articles from {ARCHIVE_URL}')
        self.driver.get(ARCHIVE_URL)
        while True:
            try:
                load_more_button = self.driver.find_element(By.CSS_SELECTOR, '.ajax_load_btn')  # Update with actual class
                if 'visibility: hidden' in load_more_button.get_attribute('style'):
                    logging.info('Load More button is hidden. Exiting loop.')
                    break
                ActionChains(self.driver).move_to_element(load_more_button).click(load_more_button).perform()
                time.sleep(2)  # Wait for new content to load
            except Exception as e:
                logging.warning('No more Load More button found or an error occurred:', exc_info=True)
                break
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        self.driver.quit()
        return soup
 
    def parsing_articles(self, soup):
        links = soup.select('.link_overlay')
        articles = []
        for link in links:
            article_url = 'https:' + link.get('href') + '?'
            logging.info(f'Fetching article data from {article_url}')
            article_data = self.fetch_article_data(url=article_url)
            if article_data:
                articles.append(article_data)
        return articles

    def fetch_article_data(self, url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            headline = soup.find('h1', class_='title').text if soup.find('h1', class_='title') else ''
            article_descriptions = soup.find('article').text if soup.find('article') else ''
            topics = soup.find('div', class_='topic_list').text if soup.find('div', class_='topic_list') else ''
            publication_date = soup.find('span', class_='tts_time').text if soup.find('span', class_='tts_time') else ''
            suggested_article_titles = soup.find('a', class_='link_overlay').text
            suggested_article_link_source = soup.find('a', class_='link_overlay') # to get the article link
            suggested_article_links = 'https:' + suggested_article_link_source.get('href') if suggested_article_titles else ''
            logging.info(f'Article fetched: {headline}')
            return {
                'headline': headline,
                'article_descriptions': article_descriptions,
                'topics': topics,
                'publication_date': publication_date,
                'suggested_article_titles': suggested_article_titles,
                'suggested_article_links': suggested_article_links,
                'crawl_date': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error fetching article data from {url}: {e}")
            return None
    
    def get_article_urls(self):
        # this function is to pass the abstract method of the parent class
        pass
    
    def parse_article(self):
        # this function is to pass the abstract method of the parent class
        pass
    
    def crawl(self):
        logging.info('Starting crawl process')
        source_code = self.load_all_article()
        articles = self.parsing_articles(soup=source_code)
        for article in articles:
            try:
                self.save_to_elasticsearch(article)
                logging.info(f"Saved article: {article['headline']}")
            except Exception as e:
                logging.error(f"Error saving article to Elasticsearch: {e}")
        logging.info('Crawling Completed')


if __name__ == '__main__':
    crawler = IttefaqCrawler()
    crawler.crawl()