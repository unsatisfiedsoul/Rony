from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

def crawl(base_url):
    urls = set()

    try:
        r = requests.get(f"http://{base_url}", timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")

        for link in soup.find_all("a"):
            href = link.get("href")

            if not href:
                continue

            full_url = urljoin(f"http://{base_url}", href)
            parsed = urlparse(full_url)

            # ✅ ONLY keep same domain
            if base_url in parsed.netloc:
                urls.add(full_url)

    except:
        pass

    return list(urls)
