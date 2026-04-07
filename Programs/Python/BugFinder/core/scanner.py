from modules import xss, sqli, lfi, open_redirect
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# ❌ Skip useless file types
BLACKLIST_EXT = [
    ".jpg", ".png", ".jpeg", ".gif", ".css",
    ".svg", ".woff", ".ttf", ".ico", ".pdf"
]

def is_valid_url(url):
    try:
        parsed = urlparse(url)

        # Must have parameters
        if "=" not in url:
            return False

        # Skip static files
        if any(parsed.path.endswith(ext) for ext in BLACKLIST_EXT):
            return False

        return True
    except:
        return False


def scan_target(url):
    findings = []

    print(f"[+] Testing: {url}")

    try:
        findings += xss.scan(url)
        findings += sqli.scan(url)
        findings += lfi.scan(url)
        findings += open_redirect.scan(url)
    except:
        pass

    return findings


def run_scans(urls, threads=10):
    # ✅ Deduplicate + filter
    urls = list(set(urls))
    filtered_urls = [u for u in urls if is_valid_url(u)]

    print(f"[+] Filtered {len(filtered_urls)} valid URLs")

    results = []

    # ⚡ Multith

def is_reflected(url, payload="test123"):
    import requests

    test_url = url + payload
    try:
        r = requests.get(test_url, timeout=5)
        return payload in r.text
    except:
        return False
