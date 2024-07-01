import requests

from bs4 import BeautifulSoup


URL = 'https://www.amarsangbad.com/archive?txtDate=26/06/2024'
response = requests.get(URL)

soup = BeautifulSoup(response.text, 'html.parser')

links = soup.select('.archive-news a')

for link in links:
    link = link.get('href')
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')
    headline_title = soup.find('h1')
    finding_date = soup.select('.post-text p')
    publication_date = finding_date[1].text
    article_description = soup.select_one('article').text
    topics = soup.select('.tag-ul li a')
    suggested_article_titles = soup.select('.more-news-single .more-news-single-text h3')
    suggested_article_links = soup.select('.more-news-single a')
    for suggested_article_link in suggested_article_links:
        print(suggested_article_link.get('href'))
    
    # for suggested_article_title in suggested_article_titles:
    #     print(suggested_article_title.text)
    