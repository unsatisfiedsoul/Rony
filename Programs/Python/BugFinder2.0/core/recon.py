import subprocess

# ✅ Subdomain Enumeration
def get_subdomains(domain):
    subs = set()

    try:
        result = subprocess.check_output(
            ["subfinder", "-d", domain],
            stderr=subprocess.DEVNULL
        ).decode().splitlines()

        for sub in result:
            subs.add(sub)

    except:
        pass

    # fallback
    if not subs:
        subs.add(domain)

    return list(subs)


# ✅ URL Collection (gau + wayback)
def get_urls(domain):
    urls = set()

    try:
        gau = subprocess.check_output(
            ["gau", domain],
            stderr=subprocess.DEVNULL
        ).decode().splitlines()

        wayback = subprocess.check_output(
            ["waybackurls", domain],
            stderr=subprocess.DEVNULL
        ).decode().splitlines()

        for u in gau + wayback:
            urls.add(u)

    except:
        pass

    return list(urls)
