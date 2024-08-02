# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.action_chains import ActionChains
# from bs4 import BeautifulSoup
# import time

# import requests


# driver = webdriver.Chrome()

# # URL = 'https://www.prothomalo.com/search'

# URL = 'https://www.prothomalo.com/search?published-before=1719770399999&published-after=1719684000000'
# driver.get(URL)
# time.sleep(3)
# # Find the date picker input field and set the value
# # date_picker = driver.find_element(By.CSS_SELECTOR, '.react-datepicker-wrapper input')
# # date_picker.clear()
# # date_picker.click()
# # time.sleep(3)
# # # Find the specific date element for today's date and click it
# # # today_date_element = driver.find_element(By.CSS_SELECTOR, '.react-datepicker__day--keyboard-selected')
# # # Find the specific date element for June 28, 2024 and click it
# # specific_date_element = driver.find_element(By.CSS_SELECTOR, '.react-datepicker__day--028')
# # specific_date_element.click()
# # time.sleep(3)
# # specific_date_element.click()

# # today_date_element.click()





# # lol_pciker.click()
# # date_picker.send_keys("২৮/০৬/২০২৪ - ২৮/০৬/২০২৪")
# # date_picker.send_keys("\n")

# # assert date_picker.get_attribute('value') == "২৮/০৬/২০২৪ - ২৮/০৬/২০২৪", "The value attribute of the input field is not as expected."

# print('succedd')

# # # Submit the form if necessary (assuming there's a submit button)
# # submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
# # submit_button.click()

# # Wait for the page to load the results
# time.sleep(15)

# # # Parse the page content with BeautifulSoup
# # soup = BeautifulSoup(driver.page_source, 'html.parser')

# # # Extract the links to the articles
# # links = soup.select('.archive-news a')

# # for link in links:
# #     link = link.get('href')
# #     response = requests.get(link)
# #     soup = BeautifulSoup(response.text, 'html.parser')
# #     headline_title = soup.find('h1')
# #     finding_date = soup.select('.post-text p')
# #     publication_date = finding_date[1].text
# #     article_description = soup.select_one('article').text
# #     topics = soup.select('.tag-ul li a')
# #     suggested_article_titles = soup.select('.more-news-single .more-news-single-text h3')
# #     suggested_article_links = soup.select('.more-news-single a')
# #     for suggested_article_link in suggested_article_links:
# #         print(suggested_article_link.get('href'))
