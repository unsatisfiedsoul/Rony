import requests
from core.payload_engine import generate_payloads
from core.validator import detect_context

def scan(urls):
    findings = []

    for url in urls:
        for context in ["html", "attr", "js"]:
            payloads = generate_payloads(context)

            for payload in payloads:
                test_url = inject(url, payload)

                try:
                    res = requests.get(test_url, timeout=5)
                    ctx = detect_context(res.text, payload)

                    if ctx in ["html", "reflected"]:
                        print(f"[🔥] XSS FOUND ({ctx}): {test_url}")
                        findings.append((test_url, payload, ctx))

                except:
                    pass

    return findings


def inject(url, payload):
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    for k in qs:
        qs[k] = payload

    return urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
