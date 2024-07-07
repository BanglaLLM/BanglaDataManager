# IN this one we have to approached differently, in this they used some javascripts liabry so there is problem getting the heading of article from the site.

# Here is the approach for this on

# Get all the links of article from the site
# get the heading and content by each one by one
# save it into a file


# imports

import requests

from bs4 import BeautifulSoup

URL = 'https://www.bd-pratidin.com/'

response = requests.get(URL)

soup = BeautifulSoup(response.text, 'html.parser')


links = soup.select('a[href*="national"], a[href*="entertainment"]')

for link in links:
    print(link.get('href'))