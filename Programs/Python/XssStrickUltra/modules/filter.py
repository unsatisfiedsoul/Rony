def filter_urls(urls):
    print("[+] Filtering URLs...")

    filtered = []

    for url in urls:
        if "=" in url and ("?" in url):
            filtered.append(url)

    print(f"[+] Filtered to {len(filtered)} param URLs")
    return filtered
