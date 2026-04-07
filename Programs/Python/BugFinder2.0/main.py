import argparse
from core.recon import get_subdomains
from core.collector import collect_urls
from core.param_discovery import extract_params
from core.scanner import run_scans
from core.reporter import save_report


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--domain", required=True, help="Target domain")
    parser.add_argument("--deep", action="store_true", help="Deep scan")

    args = parser.parse_args()

    domain = args.domain

    print(f"[+] Target: {domain}")

    subs = get_subdomains(domain)
    print(f"[+] Subdomains: {len(subs)}")

    urls = collect_urls(subs)
    print(f"[+] URLs collected: {len(urls)}")

    param_urls = extract_params(urls)
    print(f"[+] Param URLs: {len(param_urls)}")

    results = run_scans(param_urls, threads=20)

    save_report(results)


if __name__ == "__main__":
    main()
