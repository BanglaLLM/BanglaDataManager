## In this one tried to get all the articles of today's(Approx 344 articles)
import requests

from bs4 import BeautifulSoup

URL = 'https://www.dailynayadiganta.com/archive'

all_titles = []
all_links = []
all_descriptions = []



response = requests.get(URL)

soup = BeautifulSoup(response.text, 'html.parser')


# getting all the titles
titles = soup.select('.archive-news-list h1')

# gettting all the links
links = soup.select('.archive-news-list a')


# loop through all the links
for link in links:
    all_links.append(link.get('href'))

# save the titles
with open('noya_digonto/titles.txt', 'w', encoding='utf-8') as file:
    for title in all_titles:
        file.write(title)


# loop through all the titles
for title in titles:
    all_titles.append(title.text)


## save the links

with open('noya_digonto/links.txt', 'w', encoding='utf-8') as file:
    for link in all_links:
        file.write(link + '\n')
        
# loop thorugh all the links to get the descriptions of all the article

# open the links file and get all the descriptions

with open('noya_digonto/links.txt', 'r', encoding='utf-8') as file:
    for link in file:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        descriptions = soup.select('.news-content p')
        for description in descriptions:
            all_descriptions.append(description.text)
            with open('noya_digonto/descriptions.txt', 'w', encoding='utf-8') as file:
                for description in all_descriptions:
                    file.write(description + '\n')
                    file.write('\n')

