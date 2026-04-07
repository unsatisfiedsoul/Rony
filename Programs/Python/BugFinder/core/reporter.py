import json

def save_report(results):
    with open("report.json", "w") as f:
        json.dump(results, f, indent=4)

    print(f"[+] Report saved: report.json")
