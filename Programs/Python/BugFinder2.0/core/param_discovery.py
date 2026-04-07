from urllib.parse import urlparse, parse_qs

COMMON_PARAMS = ["id", "user", "file", "page", "redirect", "q", "search"]

def extract_params(urls):
    param_urls = set()

    for url in urls:
        if "=" in url:
            param_urls.add(url)
            continue

        # Add artificial params
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        for param in COMMON_PARAMS:
            param_urls.add(f"{base}?{param}=test")

    return list(param_urls)
