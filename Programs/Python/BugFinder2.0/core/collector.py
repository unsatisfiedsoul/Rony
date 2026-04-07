import subprocess

def collect_urls(subdomains):
    urls = set()

    for sub in subdomains:
        try:
            gau = subprocess.check_output(["gau", sub]).decode().splitlines()
            wayback = subprocess.check_output(["waybackurls", sub]).decode().splitlines()

            for u in gau + wayback:
                urls.add(u)

        except:
            pass

    return list(urls)
