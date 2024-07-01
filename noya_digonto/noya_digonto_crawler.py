import requests

from bs4 import BeautifulSoup


# TODO add those data into database model



URL = 'https://www.dailynayadiganta.com/archive/2024-06-28'
response = requests.get(URL)
soup = BeautifulSoup(response.text, 'html.parser')


titles = soup.select('.archive-news-list h1')
links = soup.select('.archive-news-list a')
# for title in titles:
#     print(title.text)


for link in links:
    link = link.get('href')
    print(link)
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')
    headline = soup.select('.headline')
    finding_links = soup.select_one('.article-info ul li')
    publication_date = finding_links.find_next('li')
    article_descriptions = soup.select('.news-content')
    suggested_article_titles = soup.select('strong')
    suggested_article_links = soup.select('.news-title h3 a')
    category = soup.select('.breadcrumb li a')
    
    
    
    # for topic in category:
    #     print(topic.text)
    
    
    # for article in suggested_article:
    #     print(article.text)
    
    
    # for article in article_descriptions:
    #     print(article.text)


    #  print(publication_date.text)
    # print(publication_date.text)
    # print(publication_date.text)