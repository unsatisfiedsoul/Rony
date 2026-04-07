import argparse
from core.recon import get_subdomains
from core.crawler import crawl
from core.scanner import run_scans
from core.reporter import save_report
from core.recon import get_subdomains, get_urls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()

    print(f"[+] Target: {args.domain}")

    subs = get_subdomains(args.domain)
    print(f"[+] Found {len(subs)} subdomains")

    all_urls = []
    for sub in subs:
        urls = get_urls(sub)
        all_urls.extend(urls)

    print(f"[+] Collected {len(all_urls)} URLs")

    results = run_scans(all_urls)

    save_report(results)

if __name__ == "__main__":
    main()
