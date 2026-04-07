from urllib.parse import urlparse, parse_qs

def extract_params(urls):
    print("[+] Mining parameters...")

    result = []

    for url in urls:
        if "?" in url and "=" in url:
            result.append(url)

    print(f"[DEBUG] Param URLs Found: {len(result)}")  # 👈 ADD THIS

    return result
