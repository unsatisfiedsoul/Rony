import argparse
from core.engine import run

def main():
    parser = argparse.ArgumentParser(description="XSS Auto Pro CLI")
    parser.add_argument("-u", "--url", help="Target URL")
    parser.add_argument("-d", "--domain", help="Target Domain")
    parser.add_argument("--deep", action="store_true", help="Deep Scan Mode")
    parser.add_argument("--threads", type=int, default=10)

    args = parser.parse_args()

    run(args)

if __name__ == "__main__":
    main()
