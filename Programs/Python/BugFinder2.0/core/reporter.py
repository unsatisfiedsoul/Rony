def save_report(results):
    import json

    unique = [dict(t) for t in {tuple(d.items()) for d in results}]

    with open("report.json", "w") as f:
        json.dump(unique, f, indent=4)

    print(f"[+] Saved {len(unique)} unique findings")
