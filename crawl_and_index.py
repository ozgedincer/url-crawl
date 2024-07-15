import requests
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
import hashlib
from datetime import datetime

# Elasticsearch bağlantısını oluştur
es = Elasticsearch(['http://localhost:9200'])

def crawl_and_save(url):
    # URL'ye GET isteği yap
    response = requests.get(url)

    if response.status_code == 200:
        # HTML içeriği ayrıştır
        soup = BeautifulSoup(response.content, 'html.parser')

        # Haber başlıklarını ve URL'lerini seç
        articles = soup.select('div.col-lg-4.d-flex.align-items-center.mb-4, div.news-card')

        for article in articles:
            title = None
            link = None
            
            # Farklı seçicilerle başlık ve URL'yi al
            a_tag = article.find('a', class_='news-card-footer')
            if a_tag:
                title = a_tag.get_text(strip=True)
                link = a_tag['href']
            else:
                a_tag = article.find('a')
                if a_tag:
                    title_tag = a_tag.find('span', class_='fw-bold')
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                    link = a_tag['href']

            if link and title:
                # Tam URL oluştur
                if not link.startswith('http'):
                    link = "https://www.sozcu.com.tr" + link

                # Her haberin URL'sine gidip içeriğini çek
                article_response = requests.get(link)
                if article_response.status_code == 200:
                    article_soup = BeautifulSoup(article_response.content, 'html.parser')
                    content_div = article_soup.find('div', class_='content-element')
                    content = content_div.get_text(strip=True) if content_div else 'No content found'

                    doc_id = hashlib.md5(link.encode()).hexdigest()

                    doc = {
                        'url': link,
                        'title': title,
                        'content': content,
                        'timestamp': datetime.now()
                    }

                    es.index(index='web_crawler', id=doc_id, body=doc)

                    print(f"Indexed content from {link}")
                else:
                    print(f"Failed to retrieve content from {link}, status code: {article_response.status_code}")
    else:
        print(f"Failed to retrieve content from {url}, status code: {response.status_code}")

url = "https://www.sozcu.com.tr/"
crawl_and_save(url)

