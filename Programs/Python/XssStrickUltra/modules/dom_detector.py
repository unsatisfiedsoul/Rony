import requests

SOURCES = ["location", "document.URL", "document.referrer"]
SINKS = ["innerHTML", "document.write", "eval", "outerHTML"]

def detect_dom_xss(js_files):
    print("[+] Checking DOM XSS patterns...")

    findings = []

    for js in js_files:
        try:
            res = requests.get(js, timeout=5)
            content = res.text

            for s in SOURCES:
                for sink in SINKS:
                    if s in content and sink in content:
                        print(f"[🔥] Possible DOM XSS: {js}")
                        findings.append(js)

        except:
            pass

    return findings
