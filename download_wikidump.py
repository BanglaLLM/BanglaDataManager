import requests
from tqdm import tqdm

import requests
from bs4 import BeautifulSoup
from lxml import etree
import mwparserfromhell

def get_wikidump_file_size(url):
    response = requests.head(url)
    size = response.headers.get('content-length', 0)
    return int(size)

def get_latest_bengali_wiki_dump_url():
    # URL to Wikimedia dump page for Bengali Wikipedia
    url = "https://dumps.wikimedia.org/bnwiki/latest/"

    # Send a request to the URL
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the link to the latest articles dump
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and 'pages-articles.xml.bz2' in href:
            full_url = url + href
            size_in_bytes = get_wikidump_file_size(full_url)
            return full_url, size_in_bytes


def download_wikidump(url, filename):
    response = requests.get(url, stream=True)

    with open(filename, "wb") as file:
        total_length = int(response.headers.get('content-length'))
        for data in tqdm(iterable=response.iter_content(chunk_size=4096), total=total_length//4096, unit='KB'):
            file.write(data)



def extract_titles(xml_file):
    # Parse the XML file
    context = etree.iterparse(xml_file, events=('end',), tag='{http://www.mediawiki.org/xml/export-0.10/}title')

    for event, elem in context:
        print(elem.text)
        # It's safe to call clear() here because no descendants will be accessed
        elem.clear()
        # Also eliminate now-empty references from the root node to <Title>
        while elem.getprevious() is not None:
            del elem.getparent()[0]


def extract_sections(xml_file):
    # Parse the XML file
    context = etree.iterparse(xml_file, events=('end',), tag='{http://www.mediawiki.org/xml/export-0.10/}text')

    pc = 0
    for event, elem in context:
        pc += 1
        wikicode = mwparserfromhell.parse(elem.text)
        for section in wikicode.get_sections(levels=[2, 3, 4, 5, 6]):
            title = section.filter_headings()
            if title:
                print(title[0].title.strip_code().strip())
        
        # Clear the element to save memory
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
            
        if pc > 100:
            break




def main():
    dump_url, size_in_bytes = get_latest_bengali_wiki_dump_url()
    
    print(f"Bengali Latest Wiki Dump URL: {dump_url}")
    print(f"Size: {size_in_bytes} bytes ({size_in_bytes/1024/1024/1024} GB)")
    
    filename = "bnwiki-latest-pages-articles.xml.bz2"

    #download_wikidump(dump_url, filename)
    
    #extract_titles('bnwiki-latest-pages-articles.xml')
    
    extract_sections('bnwiki-latest-pages-articles.xml')
    
    print("hey")

if __name__ == '__main__':
    main()

