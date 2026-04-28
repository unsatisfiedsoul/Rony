import requests

# Set a custom user-agent to avoid being blocked by basic firewalls
headers = {
    "User-Agent": "Security-Scanner-v1.0"
}

def scan_redirects(file_path):
    try:
        with open(file_path, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
            
        if not urls:
            print("[-] Error: urls.txt is empty.")
            return

        print(f"[*] Loaded {len(urls)} URLs. Starting scan...\n")

        with requests.Session() as session:
            for url in urls:
                # Ensure the URL has a scheme
                if not url.startswith("http"):
                    url = "https://" + url

                # The parameter we are testing
                test_url = f"{url}?redirect=https://google.com"
                
                try:
                    # Timeout is important so the script doesn't hang on dead sites
                    r = session.get(test_url, headers=headers, allow_redirects=False, timeout=10)
                    
                    # Heartbeat: This shows you the script is actually doing something
                    print(f"[#] Testing: {url} | Status: {r.status_code}")

                    # Check Location header for the redirect target
                    location = r.headers.get("Location", "")
                    
                    # Logic to catch the vulnerability
                    if r.status_code in [301, 302, 303, 307, 308] and "google.com" in location:
                        print(f"\n[VULN] Found Open Redirect!")
                        print(f"Target: {test_url}")
                        print(f"Redirects to: {location}\n" + "-"*30)
                        
                except requests.exceptions.RequestException as e:
                    print(f"[!] Connection failed for {url}: {e}")

    except FileNotFoundError:
        print("[-] Error: urls.txt not found. Please create it in the same directory.")

if __name__ == "__main__":
    scan_redirects("urls.txt")
