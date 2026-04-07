import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def crawl_urls(target):
    print("[+] Crawling URLs...")
    urls = set()

    try:
        res = requests.get(target, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        for link in soup.find_all("a", href=True):
            full_url = urljoin(target, link["href"])
            urls.add(full_url)

    except Exception as e:
        print(f"[-] Crawl error: {e}")

    print(f"[+] Found {len(urls)} URLs")
    return list(urls)
