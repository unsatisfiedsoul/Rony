import requests

payloads = ['<script>alert(1)</script>']

def scan(url):
    results = []

    for payload in payloads:
        test_url = f"{url}?q={payload}"

        try:
            r = requests.get(test_url, timeout=5)

            if payload in r.text:
                results.append({
                    "type": "XSS",
                    "url": test_url
                })

        except:
            pass

    return results
