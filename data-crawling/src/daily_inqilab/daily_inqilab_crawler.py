import sys
import os
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
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
    
    def get_article_urls(self):
        logging.info("Getting article URLs from archive: %s", ARCHIVE_URL)
        soup = self.fetch_page(url=ARCHIVE_URL)
        pagination = soup.select('.single-archive-item .pagination a')
        if len(pagination) >= 3:
            third_last_link = pagination[-3] # getting the third last link which contains the information that how many page we have to crawl
            href = third_last_link.get('href')
            parsed_url = urlparse(href)
            page_number = parse_qs(parsed_url.query).get('page', [None])[0]
            number_of_pages = int(page_number)
            logging.info("Total number of pages to crawl: %d", number_of_pages)
            COUNT_PAGE_NUMBER = 1
            all_articles_urls = []
            while COUNT_PAGE_NUMBER <= number_of_pages:
                url = f'{ARCHIVE_URL}&page={COUNT_PAGE_NUMBER}'
                logging.info("Fetching articles from page: %d", COUNT_PAGE_NUMBER)
                soup = self.fetch_page(url)
                articles_urls  = soup.select('h3 a')
                for article in articles_urls:
                    article_url = article.get('href')
                    all_articles_urls.append(article_url)
                COUNT_PAGE_NUMBER += 1
            logging.info("Total articles found: %d", len(all_articles_urls))
            return all_articles_urls
            
    def parse_article(self, article_url):
        logging.info("Parsing article: %s", article_url)
        soup = BeautifulSoup(article_url, 'html.parser')
        headline = soup.select_one('.col-md-9 h2').text
        print(headline)
        article_descriptions = soup.select('.new-details .description p')
        article_content = ""
        for i in article_descriptions:
            article_content += i.text + "\n"
        publication_date = soup.select_one('.news-date-time').text
        category = soup.select_one('.col-md-9 p a') # the category is being fetched from the last one not from the head of the source
        suggested_article_links = ""
        # some extra things are came back with the request for suggested title and links so we need to filter those out to make it more reliable,
        # those extra things are in the exclude_title or links variable
        exclude_urls = [
            'https://dailyinqilab.com',
            'https://dailyinqilab.com/national',
            'javascript:void(0)',
            'http://www.htmlcommentbox.com'
        ]
        for link in soup.select('.mt-3 a'):
            url = link.get('href')
            if url not in exclude_urls:
                suggested_article_links += url + "\n"
        # suggested article titles
        exclude_titles = [
            'জাতীয়',
            'অনলাইন ডেস্ক',
            'HTML Comment Box',
            'আরও'
        ]
        suggested_article_titles = ""
        for title in soup.select('.mt-3 a'):
            if title.text.strip() not in exclude_titles:
                suggested_article_titles += title.text.strip() + '\n'        
        logging.info("Article parsed successfully: %s", article_url)
        return {
            "headline": headline,
            "content": article_content,
            "publication_date": publication_date,
            "category": category,
            "suggested_article_links": suggested_article_links,
            "suggested_article_titles": suggested_article_titles
        }


    def main(self):
        logging.info("Starting main process")
        all_urls = self.get_article_urls()
        for article_url in all_urls:
            article_data = self.parse_article(article_url)
            logging.info("Article data fetched successfully")
            print(article_data)

if __name__ == "__main__":
    init = DailyInqilabCrawler()
    init.main()