#!/usr/bin/env python3
import os
import shutil
import subprocess

# -----------------------------
# Helper functions
# -----------------------------
def run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        print(f"[!] Error running: {cmd}")

def is_installed(binary):
    return shutil.which(binary) is not None

def pkg_install(pkg):
    print(f"[+] Installing {pkg}...")
    run_cmd(f"pkg install -y {pkg}")

def pip_install(pkg):
    print(f"[+] Installing {pkg} via pip...")
    run_cmd(f"pip install {pkg}")

def go_install(pkg):
    print(f"[+] Installing {pkg} via go...")
    run_cmd(f"go install -v {pkg}")

# -----------------------------
# Update system
# -----------------------------
print("[*] Updating packages...")
run_cmd("pkg update -y && pkg upgrade -y")

# -----------------------------
# Install Go
# -----------------------------
if not is_installed("go"):
    pkg_install("golang")

# -----------------------------
# Setup PATH
# -----------------------------
bashrc_path = os.path.expanduser("~/.bashrc")

def add_to_path(line):
    if os.path.exists(bashrc_path):
        with open(bashrc_path, "r") as f:
            content = f.read()
    else:
        content = ""

    if line not in content:
        print(f"[+] Adding to PATH: {line}")
        with open(bashrc_path, "a") as f:
            f.write("\n" + line + "\n")

# Add Go bin
add_to_path('export PATH=$PATH:$(go env GOPATH)/bin')

# Add tools dir
tools_dir = os.path.expanduser("~/tools")
os.makedirs(tools_dir, exist_ok=True)
add_to_path(f'export PATH=$PATH:{tools_dir}')

# Reload bashrc
run_cmd(f"source {bashrc_path}")

# -----------------------------
# PKG tools
# -----------------------------
pkg_tools = {
    "nmap": "nmap",
    "nc": "netcat-openbsd",
    "curl": "curl",
    "git": "git",
    "python3": "python",
    "ssh": "openssh",
    "proxychains4": "proxychains-ng",
    "feroxbuster": "feroxbuster",
    "dirb": "dirb",
    "snmpwalk": "net-snmp",
    "sslscan": "sslscan",
    "lsof": "lsof",
    "wget": "wget",
    "termux-open-url": "termux-tools"
}

# -----------------------------
# PIP tools
# -----------------------------
pip_tools = [
    "dnsrecon",
    "fierce"
]

# -----------------------------
# GO tools
# -----------------------------
go_tools = {
    "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
    "dnsx": "github.com/projectdiscovery/dnsx/cmd/dnsx@latest",
    "gau": "github.com/lc/gau/v2/cmd/gau@latest",
    "waybackurls": "github.com/tomnomnom/waybackurls@latest",
    "naabu": "github.com/projectdiscovery/naabu/v2/cmd/naabu@latest",
    "httpx": "github.com/projectdiscovery/httpx/cmd/httpx@latest",
    "nuclei": "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
    "ffuf": "github.com/ffuf/ffuf/v2@latest",
    "gobuster": "github.com/OJ/gobuster/v3@latest",
    "chisel": "github.com/jpillora/chisel@latest"
}

# -----------------------------
# Install PKG tools
# -----------------------------
print("\n[*] Installing pkg tools...")
for binary, package in pkg_tools.items():
    if not is_installed(binary):
        pkg_install(package)
    else:
        print(f"[✓] {binary} already installed")

# -----------------------------
# Install PIP tools
# -----------------------------
print("\n[*] Installing pip tools...")
for tool in pip_tools:
    if not is_installed(tool):
        pip_install(tool)
    else:
        print(f"[✓] {tool} already installed")

# -----------------------------
# Install GO tools
# -----------------------------
print("\n[*] Installing Go tools...")
for binary, pkg in go_tools.items():
    if not is_installed(binary):
        go_install(pkg)
    else:
        print(f"[✓] {binary} already installed")

# -----------------------------
# Install Git-based tools
# -----------------------------
def install_git_tools(file_path="git_tools.txt"):
    if not os.path.exists(file_path):
        print("[!] git_tools.txt not found!")
        return

    print("\n[*] Installing Git-based tools...")

    with open(file_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        if "|" not in line:
            continue

        tool, cmd = line.strip().split("|")
        tool_path = os.path.expanduser(f"~/tools/{tool}")

        if not os.path.exists(tool_path):
            print(f"[+] Installing {tool} from Git...")
            run_cmd(cmd)
        else:
            print(f"[✓] {tool} already installed")

install_git_tools()

# -----------------------------
# Done
# -----------------------------
print("\n🔥 All tools installed & ready!")
print("👉 Restart Termux or run: source ~/.bashrc")
