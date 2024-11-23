import requests
import xml.etree.ElementTree as ET

def upload_url(scraping_url):
    url = "http://localhost:1865/rabbithole/web"

    payload = {
        "url": scraping_url,
        "metadata": {
            "category": "cheshire-cat-docs"
        }
    }
    # print(f"payload: {payload}")
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)


def extract_urls_from_file(file_path, start=0, end=5):
    # Analizza il contenuto XML dal file
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Estrai tutti gli URL
    urls = []
    for url in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
        loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        if loc is not None:
            urls.append(loc.text)
    
    # Stampa gli URL
    print(len(urls))
    for idx, url in enumerate(urls):
        if idx < start:
            continue

        if idx == end:
            break
        
        print(idx, url)
        upload_url(url)

if __name__ == "__main__":
    file_path = "cheshire-doc-sitemap.xml"

    extract_urls_from_file(file_path, 0, 100)
    # upload_url("https://cheshire-cat-ai.github.io/docs/")
