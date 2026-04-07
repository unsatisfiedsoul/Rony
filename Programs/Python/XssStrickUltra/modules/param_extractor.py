from urllib.parse import urlparse, parse_qs

def extract_params(urls):
    print("[+] Extracting parameters...")

    final = []

    for url in urls:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)

        if qs:
            final.append(url)

    print(f"[+] Found {len(final)} usable URLs")
    return final
