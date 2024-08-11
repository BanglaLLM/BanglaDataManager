import sys
import os
from datetime import datetime
import logging

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_crawler import NewsCrawler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KalerKonthoCrawler(NewsCrawler):
    def __init__(self, es_host='localhost', es_port=9200):
        super().__init__('https://www.kalerkantho.com', es_host, es_port)
    
    def get_article_urls(self, date):
        archive_url = f'{self.base_url}/archive/{date.strftime("%Y-%m-%d")}'
        soup = self.fetch_page(archive_url)
        if soup is None:
            logging.error(f"Failed to fetch archive page for date: {date}")
            return []
        links = [a['href'] for a in soup.select('.card a') if 'card-header' not in a.parent.get('class', [])]
        return [f'{self.base_url}{link}' for link in links]
    
    def parse_article(self, article_url):
        soup = self.fetch_page(article_url)
        if soup is None:
            logging.error(f"Failed to fetch article page: {article_url}")
            return None
        
        try:
            headline = soup.find('h1')
            headline_text = headline.text.strip() if headline else ''
            
            article_description = soup.select('article')
            content = ' '.join([desc.text.strip() for desc in article_description])
            
            publication_date = soup.find('time')
            pub_date = publication_date.text.strip() if publication_date else ''
            
            topics = [topic.text.strip() for topic in soup.select('.card-body ul li a')]
            
            suggested_articles = []
            for title, link in zip(soup.select('.widget ul li h5'), soup.select('.widget ul li a')):
                suggested_articles.append({
                    'title': title.text.strip(),
                    'link': f'{self.base_url}{link.get("href")}'
                })
            
            article = {
                'url': article_url,
                'headline': headline_text,
                'article_descriptions': content,
                'publication_date': pub_date,
                'topics': topics,
                'suggested_articles': suggested_articles,
                'crawl_date': datetime.now().isoformat()
            }
            
            return article
        except Exception as e:
            logging.error(f"Error parsing article {article_url}: {e}")
            return None

def main():
    crawler = KalerKonthoCrawler()
    today = datetime.now().date()
    articles = crawler.get_all_articles_of_date(today)
    logging.info(f"Crawled {len(articles)} articles from Kaler Kontho for {today}")
    
    if not crawler.es_available:
        logging.warning("Elasticsearch is not available. Articles were not saved to the database.")
        logging.info("To save articles, ensure Elasticsearch is running and modify the code to connect.")
    
    # Optionally, you can process or save the articles in a different way here
    # For example, you could save them to a file:
    # with open(f'kaler_kontho_articles_{today}.txt', 'w', encoding='utf-8') as f:
    #     for article in articles:
    #         f.write(f"Headline: {article['headline']}\n")
    #         f.write(f"URL: {article['url']}\n")
    #         f.write(f"Content: {article['content'][:500]}...\n\n")

if __name__ == "__main__":
    main()