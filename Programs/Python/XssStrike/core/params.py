from urllib.parse import urlparse, parse_qs

def extract_params(urls):
    print("[+] Extracting parameters...")
    param_urls = []

    for url in urls:
        parsed = urlparse(url)
        if parsed.query:
            param_urls.append(url)

    print(f"[+] Found {len(param_urls)} URLs with parameters")
    return param_urls
