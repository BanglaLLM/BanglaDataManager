import requests

from bs4 import BeautifulSoup

URL = 'https://www.ittefaq.com.bd/'

response = requests.get(URL)

soup = BeautifulSoup(response.text, 'html.parser')


all_titles = []


titles = soup.select('.title_holder .tag_title_holder .title')
for title in titles:
    all_titles.append(title.text)



with open('ittefaq/titles.txt', 'w', encoding='utf-8') as file:
    for title in all_titles:
        file.write(title)

all_links = []
links = soup.select('.title_holder .tag_title_holder .title a')

for link in links:
    all_links.append(link.get('href'))

with open('ittefaq/links.txt', 'w', encoding='utf-8') as file:
    for link in all_links:
        link = 'https:' + link
        file.write(link + '\n')
    

all_descriptions = []


with open('ittefaq/links.txt', 'r', encoding='utf-8') as f:
    for line in f:
        link = line.strip()
        print(link)
        response = requests.get(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        descriptions = soup.select('.jw_article_body')
        for description in descriptions:
            all_descriptions.append(description.text)
            print(all_descriptions)
            with open('ittefaq/descriptions.txt', 'w', encoding='utf-8') as f:
                for texts in all_descriptions:
                    f.write(texts + '\n')
                    
