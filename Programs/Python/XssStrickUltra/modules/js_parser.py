import re
import requests

def extract_js_params(js_url):
    params = set()

    try:
        res = requests.get(js_url, timeout=5)

        matches = re.findall(r"[?&]([a-zA-Z0-9_]+)=", res.text)
        params.update(matches)

    except:
        pass

    return list(params)

import re
import requests

def parse_js(js_files):
    print("[+] Parsing JS for endpoints & params...")

    endpoints = set()
    params = set()

    for js in js_files:
        try:
            res = requests.get(js, timeout=5)
            content = res.text

            # Find endpoints
            eps = re.findall(r'["\'](/api/[^"\']+)["\']', content)
            endpoints.update(eps)

            # Find parameters
            prms = re.findall(r'([a-zA-Z0-9_]+)=', content)
            params.update(prms)

        except:
            pass

    print(f"[+] Found {len(endpoints)} endpoints")
    print(f"[+] Found {len(params)} params")

    return list(endpoints), list(params)
