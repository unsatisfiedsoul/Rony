import argparse
from core.crawler import crawl_urls
from core.params import extract_params
from core.scanner import scan_xss

def main():
    parser = argparse.ArgumentParser(description="XSS Auto CLI Tool")
    parser.add_argument("-u", "--url", help="Target URL", required=True)
    args = parser.parse_args()

    target = args.url

    print(f"[+] Target: {target}")

    # Step 1: Crawl URLs
    urls = crawl_urls(target)

    # Step 2: Extract parameters
    param_urls = extract_params(urls)

    # Step 3: Scan for XSS
    scan_xss(param_urls)

if __name__ == "__main__":
    main()
