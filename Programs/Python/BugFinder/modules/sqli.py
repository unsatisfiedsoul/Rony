import requests

payloads = ["' OR '1'='1"]

def scan(url):
    results = []

    for payload in payloads:
        test_url = f"{url}?id={payload}"

        try:
            r = requests.get(test_url, timeout=5)

            if "sql" in r.text.lower():
                results.append({
                    "type": "SQLi",
                    "url": test_url
                })

        except:
            pass

    return results
