import json
from datetime import datetime

def save_results(vulns):
    filename = f"results/report_{datetime.now().strftime('%H%M%S')}.json"

    data = [{"url": v[0], "payload": v[1]} for v in vulns]

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[+] Results saved to {filename}")
