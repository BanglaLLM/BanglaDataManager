import requests

from bs4 import BeautifulSoup


# TODO Create a database to store those fetched data

URL = 'https://www.kalerkantho.com/archive/2024-06-27'
# pages = ['https://www.kalerkantho.com/print-archive/first-page/2024-06-27', 'https://www.kalerkantho.com/print-archive/last-page/2024-06-27', 'https://www.kalerkantho.com/print-archive/news/2024-06-27', 'https://www.kalerkantho.com/print-archive/news/2024-06-27', 'https://www.kalerkantho.com/print-archive/industry-business/2024-06-27', 
#          'https://www.kalerkantho.com/print-archive/sports/2024-06-27', 'https://www.kalerkantho.com/print-archive/deshe-deshe/2024-06-27', 'https://www.kalerkantho.com/print-archive/priyo-desh/2024-06-27', 'https://www.kalerkantho.com/print-archive/education/2024-06-27', 'https://www.kalerkantho.com/print-archive/editorial/2024-06-27',
#          'https://www.kalerkantho.com/print-archive/sub-editorial/2024-06-27', 'https://www.kalerkantho.com/print-archive/rangberang/2024-06-27', 'https://www.kalerkantho.com/print-archive/islamic-life/2024-06-27']



# for page in pages:
#     response = requests.get(page)
#     soup = BeautifulSoup(response.text, 'html.parser')
#     heading_titles = soup.find_all('h4')
#     for heading_title in heading_titles:
#         print(page)
#         print(heading_title.text)

response = requests.get(URL)

soup = BeautifulSoup(response.text, 'html.parser')

# main_headline_title = soup.find_all('h4', class_='card-title')
# normal_headline_title = soup.select('.card-body ul li')

links = [a['href'] for a in soup.select('.card a') if 'card-header' not in a.parent.get('class', [])]


# for title in main_headline_title:
#     print(title.text)

# for title in normal_headline_title:
#     print(title.text)

for link in links:
    link = 'https://www.kalerkantho.com' + link
    # print(link)
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')
    headline = soup.find('h1')
    article_description = soup.select('article')
    publication_date = soup.find('time')
    widget_title = soup.select('h2')
    suggested_article_titles = soup.select('.widget ul li h5')
    suggested_article_links = soup.select('.widget ul li a')
    suggested_article_links = ['https://www.kalerkantho.com' + i.get('href') for i in suggested_article_links]
    topics = soup.select('.card-body ul li a')
    

# TODO all the info is fetched now can add those into the database
    
    
    
    # for i in suggested_article_links:
    #     print(i)
    
    
    
    
    # for title in suggested_article_titles:
    #     print(title.text)
    # for widget in widget_title:
    #     print(widget.text)
    #     if widget.text == 'সর্বাধিক পঠিত':
    #         print('succeed')
            
    # print(publication_date.text)
    # for title in suggested_article_title:
    #     print(title.text)
    # if headline is not None:
    #     print(headline.text)
    # if article_description is not None:
    # print(article_description)
    # for description in article_description:
    #     print(description.text)
