from modules.recon import subdomain_enum
from modules.crawler import crawl
from modules.param_miner import extract_params
from modules.xss_engine import scan

from modules.js_collector import collect_js
from modules.js_parser import parse_js
from modules.dom_detector import detect_dom_xss


def run(args):
    print("\n[⚡] XSS ULTRA STARTED\n")

    # Step 1: Recon
    targets = subdomain_enum(args.domain)

    # Step 2: Crawl
    urls = crawl(targets)

    # Step 3: Param Mining
    params = extract_params(urls)

    # 🔥 Step 4: JS HUNTER MODE (FIXED POSITION)
    js_files = collect_js(urls)

    endpoints, hidden_params = parse_js(js_files)

    dom_xss = detect_dom_xss(js_files)

    # Convert JS endpoints → URLs
    js_urls = []
    for ep in endpoints:
        for p in hidden_params:
            js_urls.append(f"https://{args.domain}{ep}?{p}=test")

    params.extend(js_urls)

    # Step 5: XSS Scan
    vulns = scan(params)

    print(f"\n[🔥] Total Vulns Found: {len(vulns)}")
    print("\n[✔] Done\n")
