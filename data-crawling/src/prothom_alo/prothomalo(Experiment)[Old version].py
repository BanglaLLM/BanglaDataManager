import requests

from bs4 import BeautifulSoup


URL = 'https://www.prothomalo.com/'

response = requests.get(URL)

soup = BeautifulSoup(response.text, 'html.parser')

titles = soup.find_all('h3', class_='headline-title')

links = soup.select('.title-link')

descriptions = soup.select('.story-element-text')


all_links = []
all_titles = []
all_descriptions = []



for link in links:
    all_links.append(link.get('href'))
    with open('protom_alo_links.txt', 'w', encoding='utf-8') as f:
        for links in all_links:
            f.write(links + '\n')
        




for title in titles:
    main = title.select('span.tilte-no-link-parent')
    all_titles.append(main[0].text)
    with open('protom_alo_titles.txt', 'w', encoding='utf-8') as f:
        for titles in all_titles:
            f.write(titles + '\n')


with open('links.txt', 'r', encoding='utf-8') as f:
    for line in f:
        link = line.strip()
        # print(link)
        response = requests.get(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        descriptions = soup.select('p')
        for description in descriptions:
            all_descriptions.append(description.text)
            print(all_descriptions)
            with open('protom_alo_descriptions.txt', 'w', encoding='utf-8') as f:
                for texts in all_descriptions:
                    f.write(texts)
                    f.write('\n')
                    f.write('\n')
                    f.write('\n')
