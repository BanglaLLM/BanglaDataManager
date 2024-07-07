from crewai import Agent, Task, Crew
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from elasticsearch import Elasticsearch

# Initialize Elasticsearch client
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

class WebCrawlerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Web Crawler Agent",
            goal="Crawl websites and extract information",
            backstory="I am an AI agent designed to crawl websites, extract information, and save it to a database."
        )
        self.driver = webdriver.Chrome()  # You may need to specify the path to chromedriver

    def get_page_content(self, url):
        self.driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Scroll to the bottom of the page
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Try to click "Next" button if it exists
        try:
            next_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
            )
            next_button.click()
        except:
            pass  # No "Next" button found

        return self.driver.page_source

    def extract_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        return [a['href'] for a in soup.find_all('a', href=True)]

    def parse_content(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else "No title"
        text = soup.get_text(separator=' ', strip=True)
        return title, text

    def save_to_elasticsearch(self, url, title, text):
        doc = {
            'url': url,
            'title': title,
            'text': text
        }
        es.index(index="web_crawl", body=doc)

    def crawl_website(self, url):
        visited = set()
        to_visit = [url]

        while to_visit:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue

            visited.add(current_url)
            print(f"Crawling: {current_url}")

            try:
                html = self.get_page_content(current_url)
                title, text = self.parse_content(html)
                self.save_to_elasticsearch(current_url, title, text)

                links = self.extract_links(html)
                to_visit.extend([link for link in links if link.startswith(url) and link not in visited])
            except Exception as e:
                print(f"Error crawling {current_url}: {str(e)}")

        self.driver.quit()

# Create the agent
web_crawler = WebCrawlerAgent()

# Create a task for the agent
crawl_task = Task(
    description="Crawl the given website and save extracted information to Elasticsearch",
    agent=web_crawler
)

# Create a crew with the agent and task
crew = Crew(
    agents=[web_crawler],
    tasks=[crawl_task]
)

# Run the crew
result = crew.kickoff()

# Use the agent to crawl a specific website
web_crawler.crawl_website("https://prothom-alo.com")