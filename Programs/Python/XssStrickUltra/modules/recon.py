import subprocess

def subdomain_enum(domain):
    print("[+] Running Subdomain Enumeration...")

    try:
        result = subprocess.run(
            ["subfinder", "-d", domain, "-silent"],
            capture_output=True,
            text=True,
            timeout=60   # ⏱️ 60 sec timeout
        )

        domains = result.stdout.splitlines()

    except subprocess.TimeoutExpired:
        print("[!] Subfinder timed out — continuing...")
        domains = []

    print(f"[+] Found {len(domains)} subdomains")
    return domains
