## in this one I will also use the archieve to get all the news of today

import requests

from bs4 import BeautifulSoup


URL = 'https://www.amarsangbad.com/archive'


response = requests.get(URL)

# empty dictionaries to store values
all_headings = []
all_links = []


soup = BeautifulSoup(response.text, 'html.parser')


# fetching all the headings
headings = soup.select('.archive-news-heading h3')

# fetching all the links of those articles
links = soup.select('.archive-news a')

# getting all the reference links
for link in links:
    all_links.append(link.get('href'))

    # save those links into a text file

    with open('amr_sangbad/articles_links.txt', 'w', encoding='utf-8') as file:
        for link in all_links:
            file.write(link + '\n')


# adding all the headings and saving those into a text file
for heading in headings:
    all_headings.append(heading.text)

    with open('amr_sangbad/amr_songbad_headings.txt', 'w', encoding='utf-8') as file:
        for heading in all_headings:
            file.write(heading + '\n')