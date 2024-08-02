from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time

import requests




# TODO Create a database to store those fetched data
# Due to unavailability of c++ build tool the sqlite is failed to installed in my machine. For that I will handle it later



 # Run in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

URL = 'https://www.ittefaq.com.bd/archive/2024-07-31'
driver.get(URL)

# Load all titles by clicking "Load More" button
while True:
    try:
        load_more_button = driver.find_element(By.CSS_SELECTOR, '.ajax_load_btn')  # Update with actual class
        if 'visibility: hidden' in load_more_button.get_attribute('style'):
            print("Load More button is hidden. Exiting loop.")
            break
        ActionChains(driver).move_to_element(load_more_button).click(load_more_button).perform()
        time.sleep(2)  # Wait for new content to load
    except Exception as e:
        print("No more 'Load More' button found or an error occurred:", e)
        break

# Parse the page content with BeautifulSoup
soup = BeautifulSoup(driver.page_source, 'html.parser')
driver.quit()
links = soup.select('.link_overlay')
titles = soup.select('.title')
print(len(titles))
for link in links:
    link = 'https:' + link.get('href') + '?'
    # refer = link.get('href')
    # print(link)
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1', class_='title')
    article_description = soup.find('article')
    topic_list = soup.find('div', class_='topic_list')
    publication_date = soup.find('span', class_='tts_time')
    suggested_article_title = soup.find('a', class_='link_overlay')
    suggested_article_links = 'https:' + suggested_article_title.get('href')
    print(title.text)
    # print(suggested_article.text)
    # print(suggested_article_links)
    # print(publication_date.text)
    # print(article_description.text)
    # print(topic_list.text)