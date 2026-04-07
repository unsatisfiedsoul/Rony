import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def collect_js(urls):
    print("[+] Collecting JS files...")

    js_files = set()

    for url in urls:
        try:
            res = requests.get(url, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")

            for script in soup.find_all("script", src=True):
                js_url = urljoin(url, script["src"])
                js_files.add(js_url)

        except:
            pass

    print(f"[+] Found {len(js_files)} JS files")
    return list(js_files)
