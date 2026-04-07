import re
import requests

def extract_js_endpoints(url):
    endpoints = set()

    try:
        r = requests.get(url, timeout=5)

        matches = re.findall(r'https?://[^\s"]+', r.text)

        for m in matches:
            endpoints.add(m)

    except:
        pass

    return list(endpoints)
