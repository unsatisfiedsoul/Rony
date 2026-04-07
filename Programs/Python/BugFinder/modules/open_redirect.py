import requests

payload = "https://evil.com"

def scan(url):
    results = []

    test_url = f"{url}?redirect={payload}"

    try:
        r = requests.get(test_url, allow_redirects=False)

        if "evil.com" in r.headers.get("Location", ""):
            results.append({
                "type": "Open Redirect",
                "url": test_url
            })

    except:
        pass

    return results
