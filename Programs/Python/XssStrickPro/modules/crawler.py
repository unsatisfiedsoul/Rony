import subprocess

def crawl(targets):
    print("[+] Crawling URLs...")

    all_urls = set()

    for target in targets:
        gau = subprocess.getoutput(f"gau {target}")
        wayback = subprocess.getoutput(f"waybackurls {target}")

        all_urls.update(gau.split("\n"))
        all_urls.update(wayback.split("\n"))

    print(f"[+] Collected {len(all_urls)} URLs")
    return list(all_urls)
