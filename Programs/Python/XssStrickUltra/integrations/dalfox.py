import subprocess

def verify_with_dalfox(url):
    print("[+] Verifying with Dalfox...")
    result = subprocess.getoutput(f"echo {url} | dalfox pipe")

    return result
