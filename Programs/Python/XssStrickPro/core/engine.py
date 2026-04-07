from modules.recon import subdomain_enum
from modules.crawler import crawl
from modules.param_extractor import extract_params
from modules.filter import filter_urls
from modules.xss_scanner import scan_xss
from core.output import save_results

def run_pipeline(args):
    print("\n[⚡] XSS-AUTO PRO STARTED\n")

    # Step 1: Recon
    targets = []
    if args.domain:
        targets = subdomain_enum(args.domain)
    elif args.url:
        targets = [args.url]

    # Step 2: Crawling
    urls = crawl(targets)

    # Step 3: Filter
    urls = filter_urls(urls)

    # Step 4: Param Extraction
    param_urls = extract_params(urls)

    # Step 5: XSS Scan
    vulns = scan_xss(param_urls, threads=args.threads)

    # Step 6: Save Results
    save_results(vulns)

    print("\n[✔] Scan Completed\n")
