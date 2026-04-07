from concurrent.futures import ThreadPoolExecutor
from modules import xss, sqli, lfi, open_redirect, ssrf

def scan_target(url):
    findings = []

    print(f"[+] Testing: {url}")

    findings += xss.scan(url)
    findings += sqli.scan(url)
    findings += lfi.scan(url)
    findings += open_redirect.scan(url)
    findings += ssrf.scan(url)

    return findings


def run_scans(urls, threads=20):
    results = []

    with ThreadPoolExecutor(max_workers=threads) as executor:
        for res in executor.map(scan_target, urls):
            if res:
                results.extend(res)

    print(f"[+] Total findings: {len(results)}")

    return results
