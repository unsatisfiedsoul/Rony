import subprocess

def subdomain_enum(domain):
    print("[+] Running Subdomain Enumeration...")

    result = subprocess.getoutput(f"subfinder -d {domain} -silent")
    domains = result.split("\n")

    print(f"[+] Found {len(domains)} subdomains")
    return domains
