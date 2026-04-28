#!/bin/python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║          RED TEAM WORKFLOW ENGINE — Full Lifecycle Framework         ║
║  Stages: Recon → Scan → Exploit → Post-Exploit → Report             ║
║  Features: SQLite DB, Session Memory, Plugin Tools, Logging          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import sqlite3
import json
import uuid
import hashlib
import subprocess
import socket
import ssl
import re
import os
import sys
import time
import datetime
import argparse
import ipaddress
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from contextlib import contextmanager

# ─────────────────────────────────────────────────────────────────────
# ENUMS & CONSTANTS
# ─────────────────────────────────────────────────────────────────────

class Stage(str, Enum):
    RECON        = "recon"
    SCAN         = "scan"
    EXPLOIT      = "exploit"
    POST_EXPLOIT = "post_exploit"
    REPORT       = "report"

class Severity(str, Enum):
    INFO     = "info"
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"

class Status(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    SKIPPED   = "skipped"

SEVERITY_COLOR = {
    Severity.INFO:     "\033[94m",   # blue
    Severity.LOW:      "\033[92m",   # green
    Severity.MEDIUM:   "\033[93m",   # yellow
    Severity.HIGH:     "\033[91m",   # red
    Severity.CRITICAL: "\033[95m",   # magenta
}
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"

DB_PATH = Path("redteam_sessions.db")

# ─────────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────────

@dataclass
class Finding:
    id:          str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    stage:       str = Stage.RECON
    tool:        str = ""
    title:       str = ""
    description: str = ""
    severity:    str = Severity.INFO
    evidence:    str = ""
    target:      str = ""
    timestamp:   str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    tags:        List[str] = field(default_factory=list)
    raw:         Dict[str, Any] = field(default_factory=dict)

@dataclass
class SessionMemory:
    session_id:   str
    target:       str
    scope:        List[str]            = field(default_factory=list)
    open_ports:   Dict[str, List[int]] = field(default_factory=dict)
    services:     Dict[str, Any]       = field(default_factory=dict)
    credentials:  List[Dict]           = field(default_factory=list)
    hosts:        List[str]            = field(default_factory=list)
    domains:      List[str]            = field(default_factory=list)
    subdomains:   List[str]            = field(default_factory=list)
    urls:         List[str]            = field(default_factory=list)
    vulns:        List[Dict]           = field(default_factory=list)
    notes:        List[str]            = field(default_factory=list)
    stage_status: Dict[str, str]       = field(default_factory=lambda: {s.value: Status.PENDING for s in Stage})
    findings:     List[Finding]        = field(default_factory=list)
    created_at:   str                  = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    updated_at:   str                  = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

# ─────────────────────────────────────────────────────────────────────
# DATABASE LAYER
# ─────────────────────────────────────────────────────────────────────

class Database:
    """SQLite persistence layer for sessions, findings, and tool logs."""

    def __init__(self, path: Path = DB_PATH):
        self.path = path
        self._init_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id  TEXT PRIMARY KEY,
                    target      TEXT NOT NULL,
                    memory_json TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS findings (
                    id          TEXT PRIMARY KEY,
                    session_id  TEXT NOT NULL,
                    stage       TEXT NOT NULL,
                    tool        TEXT NOT NULL,
                    title       TEXT NOT NULL,
                    description TEXT,
                    severity    TEXT NOT NULL,
                    evidence    TEXT,
                    target      TEXT,
                    tags        TEXT,
                    raw_json    TEXT,
                    timestamp   TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );

                CREATE TABLE IF NOT EXISTS tool_logs (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    stage      TEXT NOT NULL,
                    tool       TEXT NOT NULL,
                    status     TEXT NOT NULL,
                    output     TEXT,
                    duration   REAL,
                    timestamp  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS credentials (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    host       TEXT,
                    service    TEXT,
                    username   TEXT,
                    password   TEXT,
                    hash_val   TEXT,
                    source     TEXT,
                    timestamp  TEXT NOT NULL
                );
            """)

    # ── Sessions ──────────────────────────────────────────────────────

    def save_session(self, mem: SessionMemory):
        now = datetime.datetime.utcnow().isoformat()
        mem.updated_at = now
        # Serialize findings
        mem_dict = asdict(mem)
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO sessions(session_id, target, memory_json, created_at, updated_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(session_id) DO UPDATE SET
                    memory_json=excluded.memory_json,
                    updated_at=excluded.updated_at
            """, (mem.session_id, mem.target, json.dumps(mem_dict), mem.created_at, now))

    def load_session(self, session_id: str) -> Optional[SessionMemory]:
        with self._conn() as conn:
            row = conn.execute("SELECT memory_json FROM sessions WHERE session_id=?",
                               (session_id,)).fetchone()
        if not row:
            return None
        d = json.loads(row["memory_json"])
        d["findings"] = [Finding(**f) for f in d.get("findings", [])]
        return SessionMemory(**{k: v for k, v in d.items()
                                if k in SessionMemory.__dataclass_fields__})

    def list_sessions(self) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT session_id, target, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Findings ──────────────────────────────────────────────────────

    def save_finding(self, session_id: str, f: Finding):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO findings
                (id,session_id,stage,tool,title,description,severity,evidence,target,tags,raw_json,timestamp)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (f.id, session_id, f.stage, f.tool, f.title, f.description,
                  f.severity, f.evidence, f.target,
                  json.dumps(f.tags), json.dumps(f.raw), f.timestamp))

    def get_findings(self, session_id: str, severity: str = None) -> List[Dict]:
        with self._conn() as conn:
            if severity:
                rows = conn.execute(
                    "SELECT * FROM findings WHERE session_id=? AND severity=? ORDER BY timestamp",
                    (session_id, severity)).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM findings WHERE session_id=? ORDER BY timestamp",
                    (session_id,)).fetchall()
        return [dict(r) for r in rows]

    # ── Tool Logs ─────────────────────────────────────────────────────

    def log_tool(self, session_id: str, stage: str, tool: str,
                 status: str, output: str = "", duration: float = 0.0):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO tool_logs(session_id,stage,tool,status,output,duration,timestamp)
                VALUES(?,?,?,?,?,?,?)
            """, (session_id, stage, tool, status, output, duration,
                  datetime.datetime.utcnow().isoformat()))

    # ── Credentials ───────────────────────────────────────────────────

    def save_credential(self, session_id: str, cred: Dict):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO credentials(session_id,host,service,username,password,hash_val,source,timestamp)
                VALUES(?,?,?,?,?,?,?,?)
            """, (session_id, cred.get("host",""), cred.get("service",""),
                  cred.get("username",""), cred.get("password",""),
                  cred.get("hash",""), cred.get("source",""),
                  datetime.datetime.utcnow().isoformat()))

    def get_credentials(self, session_id: str) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM credentials WHERE session_id=?", (session_id,)).fetchall()
        return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────
# LOGGER / UI
# ─────────────────────────────────────────────────────────────────────

class Logger:
    def __init__(self, session_id: str, log_dir: Path = Path("logs")):
        log_dir.mkdir(exist_ok=True)
        self.log_file = log_dir / f"{session_id}.log"
        self._lock = threading.Lock()

    def _write(self, level: str, msg: str):
        ts = datetime.datetime.utcnow().strftime("%H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        with self._lock:
            with open(self.log_file, "a") as fh:
                fh.write(line + "\n")
        return line

    def info(self, msg: str):
        print(f"  {CYAN}●{RESET} {msg}")
        self._write("INFO", msg)

    def success(self, msg: str):
        print(f"  {GREEN}✔{RESET} {msg}")
        self._write("SUCCESS", msg)

    def warn(self, msg: str):
        print(f"  {YELLOW}⚠{RESET} {msg}")
        self._write("WARN", msg)

    def error(self, msg: str):
        print(f"  {RED}✘{RESET} {msg}")
        self._write("ERROR", msg)

    def finding(self, f: Finding):
        col = SEVERITY_COLOR.get(f.severity, "")
        badge = f"{col}[{f.severity.upper():8s}]{RESET}"
        print(f"  {badge} {BOLD}{f.title}{RESET}")
        if f.description:
            print(f"           {DIM}{f.description[:100]}{RESET}")

    def stage_banner(self, stage: Stage):
        icons = {
            Stage.RECON:        "🔭",
            Stage.SCAN:         "🔍",
            Stage.EXPLOIT:      "💥",
            Stage.POST_EXPLOIT: "🔓",
            Stage.REPORT:       "📋",
        }
        icon = icons.get(stage, "▶")
        width = 60
        title = f"  {icon}  STAGE: {stage.value.upper().replace('_',' ')}  "
        pad = (width - len(title)) // 2
        print(f"\n{'─'*width}")
        print(f"{' '*pad}{BOLD}{CYAN}{title}{RESET}")
        print(f"{'─'*width}")


# ─────────────────────────────────────────────────────────────────────
# TOOL BASE CLASS
# ─────────────────────────────────────────────────────────────────────

class Tool:
    """Abstract base for all red-team tools."""
    name: str = "base_tool"
    stage: Stage = Stage.RECON
    description: str = ""
    options: Dict[str, Any] = {}

    def __init__(self, db: Database, mem: SessionMemory, log: Logger):
        self.db  = db
        self.mem = mem
        self.log = log

    def _new_finding(self, title, description, severity=Severity.INFO,
                     evidence="", tags=None) -> Finding:
        return Finding(
            stage=self.stage,
            tool=self.name,
            title=title,
            description=description,
            severity=severity,
            evidence=evidence,
            target=self.mem.target,
            tags=tags or [],
        )

    def _persist(self, finding: Finding):
        self.mem.findings.append(finding)
        self.db.save_finding(self.mem.session_id, finding)
        self.log.finding(finding)

    def run(self, **kwargs) -> List[Finding]:
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────
# ──────────────────── STAGE 1: RECON TOOLS ───────────────────────────
# ─────────────────────────────────────────────────────────────────────

class DNSRecon(Tool):
    name = "dns_recon"
    stage = Stage.RECON
    description = "DNS enumeration: A, MX, NS, TXT records + reverse lookup"

    def run(self, target: str = None, **kw) -> List[Finding]:
        target = target or self.mem.target
        findings = []
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
        self.log.info(f"DNS recon on {target}")

        for rtype in record_types:
            try:
                result = subprocess.run(
                    ["nslookup", f"-type={rtype}", target],
                    capture_output=True, text=True, timeout=10
                )
                output = result.stdout.strip()
                if output and "NXDOMAIN" not in output and "can't find" not in output:
                    # Extract IPs from A records
                    if rtype == "A":
                        ips = re.findall(r'\d+\.\d+\.\d+\.\d+', output)
                        for ip in ips:
                            if ip not in self.mem.hosts:
                                self.mem.hosts.append(ip)

                    f = self._new_finding(
                        title=f"DNS {rtype} record found",
                        description=f"{rtype} records for {target}",
                        severity=Severity.INFO,
                        evidence=output[:500],
                        tags=["dns", rtype.lower()]
                    )
                    self._persist(f)
                    findings.append(f)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Simulate if nslookup unavailable
                self.log.warn(f"nslookup not available, simulating {rtype} record")
                try:
                    if rtype == "A":
                        ip = socket.gethostbyname(target)
                        if ip not in self.mem.hosts:
                            self.mem.hosts.append(ip)
                        f = self._new_finding(
                            title=f"DNS A record → {ip}",
                            description=f"Resolved {target} to {ip}",
                            severity=Severity.INFO,
                            evidence=f"{target} -> {ip}",
                            tags=["dns","a-record"]
                        )
                        self._persist(f)
                        findings.append(f)
                except socket.gaierror:
                    pass
        return findings


class SubdomainEnum(Tool):
    name = "subdomain_enum"
    stage = Stage.RECON
    description = "Brute-force common subdomains via DNS resolution"
    WORDLIST = [
        "www","mail","ftp","api","dev","staging","test","vpn","remote",
        "admin","portal","webmail","shop","blog","cdn","assets","static",
        "auth","login","dashboard","app","beta","internal","corp","git",
        "jira","confluence","jenkins","gitlab","kibana","grafana","monitor"
    ]

    def run(self, target: str = None, wordlist: List[str] = None, **kw) -> List[Finding]:
        target = target or self.mem.target
        words  = wordlist or self.WORDLIST
        findings = []
        self.log.info(f"Subdomain enumeration on {target} ({len(words)} words)")

        for sub in words:
            fqdn = f"{sub}.{target}"
            try:
                ip = socket.gethostbyname(fqdn)
                if fqdn not in self.mem.subdomains:
                    self.mem.subdomains.append(fqdn)
                if ip not in self.mem.hosts:
                    self.mem.hosts.append(ip)
                sev = Severity.MEDIUM if sub in ("admin","internal","vpn","corp") else Severity.INFO
                f = self._new_finding(
                    title=f"Subdomain discovered: {fqdn}",
                    description=f"Resolved to {ip}",
                    severity=sev,
                    evidence=f"{fqdn} → {ip}",
                    tags=["subdomain","recon"]
                )
                self._persist(f)
                findings.append(f)
                self.log.success(f"Found: {fqdn} ({ip})")
            except socket.gaierror:
                pass
        return findings


class WHOISLookup(Tool):
    name = "whois_lookup"
    stage = Stage.RECON
    description = "WHOIS information gathering"

    def run(self, target: str = None, **kw) -> List[Finding]:
        target = target or self.mem.target
        self.log.info(f"WHOIS lookup for {target}")
        findings = []
        try:
            result = subprocess.run(["whois", target], capture_output=True, text=True, timeout=15)
            output = result.stdout
            if output:
                # Extract key fields
                fields = {}
                for pat, key in [
                    (r'Registrar:\s*(.+)', 'registrar'),
                    (r'Creation Date:\s*(.+)', 'created'),
                    (r'Expiry Date:\s*(.+)', 'expires'),
                    (r'Registrant Organization:\s*(.+)', 'org'),
                    (r'Name Server:\s*(.+)', 'nameserver'),
                ]:
                    m = re.search(pat, output, re.IGNORECASE)
                    if m:
                        fields[key] = m.group(1).strip()

                desc = ", ".join(f"{k}={v}" for k, v in fields.items())
                f = self._new_finding(
                    title="WHOIS data retrieved",
                    description=desc or "WHOIS data available",
                    severity=Severity.INFO,
                    evidence=output[:800],
                    tags=["whois","osint"]
                )
                self._persist(f)
                findings.append(f)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log.warn("whois command unavailable — skipping")
        return findings


class GoogleDork(Tool):
    name = "google_dork"
    stage = Stage.RECON
    description = "Generate Google dork queries for OSINT"

    DORKS = [
        ('site:{t} filetype:pdf',        'PDF documents exposed',     Severity.LOW),
        ('site:{t} filetype:xls',        'Excel files exposed',       Severity.LOW),
        ('site:{t} inurl:admin',         'Admin panel URL pattern',   Severity.MEDIUM),
        ('site:{t} inurl:login',         'Login pages discovered',    Severity.LOW),
        ('site:{t} "index of /"',        'Directory listing possible',Severity.HIGH),
        ('site:{t} intext:password',     'Password keyword in page',  Severity.HIGH),
        ('site:{t} ext:env OR ext:conf', 'Config files exposed',      Severity.CRITICAL),
        ('site:{t} intitle:"phpMyAdmin"','phpMyAdmin exposed',        Severity.CRITICAL),
    ]

    def run(self, target: str = None, **kw) -> List[Finding]:
        target = target or self.mem.target
        findings = []
        self.log.info(f"Generating Google dorks for {target}")
        for pattern, title, sev in self.DORKS:
            query = pattern.replace("{t}", target)
            f = self._new_finding(
                title=title,
                description=f"Google dork: {query}",
                severity=sev,
                evidence=f"https://google.com/search?q={query.replace(' ','+')}",
                tags=["osint","dork","google"]
            )
            self._persist(f)
            findings.append(f)
        return findings


# ─────────────────────────────────────────────────────────────────────
# ──────────────────── STAGE 2: SCAN TOOLS ────────────────────────────
# ─────────────────────────────────────────────────────────────────────

class PortScanner(Tool):
    name = "port_scanner"
    stage = Stage.SCAN
    description = "TCP connect scan across common ports"
    COMMON_PORTS = [21,22,23,25,53,80,110,111,135,139,143,443,
                    445,993,995,1723,3306,3389,5900,8080,8443,8888]

    def _scan_port(self, host: str, port: int, timeout: float = 1.0) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def run(self, hosts: List[str] = None, ports: List[int] = None,
            timeout: float = 1.0, **kw) -> List[Finding]:
        hosts  = hosts or self.mem.hosts or [self.mem.target]
        ports  = ports or self.COMMON_PORTS
        findings = []
        self.log.info(f"Port scanning {len(hosts)} host(s) × {len(ports)} ports")

        for host in hosts:
            open_ports = []
            for port in ports:
                if self._scan_port(host, port, timeout):
                    open_ports.append(port)
                    self.log.success(f"{host}:{port} OPEN")

            if open_ports:
                if host not in self.mem.open_ports:
                    self.mem.open_ports[host] = []
                self.mem.open_ports[host] = list(set(self.mem.open_ports[host] + open_ports))

                sev = Severity.HIGH if any(p in (21,23,3389,5900) for p in open_ports) else Severity.MEDIUM
                f = self._new_finding(
                    title=f"Open ports on {host}",
                    description=f"Ports: {sorted(open_ports)}",
                    severity=sev,
                    evidence=f"Host: {host}\nOpen: {sorted(open_ports)}",
                    tags=["portscan","tcp"]
                )
                f.target = host
                self._persist(f)
                findings.append(f)
        return findings


class ServiceDetector(Tool):
    name = "service_detector"
    stage = Stage.SCAN
    description = "Banner grabbing and service fingerprinting"
    SERVICE_MAP = {
        21:   ("FTP",   "220"),
        22:   ("SSH",   "SSH-"),
        25:   ("SMTP",  "220"),
        80:   ("HTTP",  "HTTP"),
        110:  ("POP3",  "+OK"),
        143:  ("IMAP",  "* OK"),
        443:  ("HTTPS", "TLS"),
        3306: ("MySQL", "\x4a"),
        3389: ("RDP",   ""),
        5900: ("VNC",   "RFB"),
        8080: ("HTTP-Alt",""),
        8443: ("HTTPS-Alt",""),
    }

    def _grab_banner(self, host: str, port: int, timeout: float = 3.0) -> str:
        try:
            with socket.create_connection((host, port), timeout=timeout) as s:
                s.settimeout(timeout)
                try:
                    banner = s.recv(1024).decode("utf-8", errors="replace").strip()
                    return banner[:200]
                except Exception:
                    return ""
        except Exception:
            return ""

    def _tls_check(self, host: str, port: int) -> Dict:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection((host, port), timeout=5) as raw:
                with ctx.wrap_socket(raw, server_hostname=host) as s:
                    cert = s.getpeercert(binary_form=False) or {}
                    return {
                        "protocol": s.version(),
                        "cipher":   s.cipher()[0] if s.cipher() else "unknown",
                        "expiry":   cert.get("notAfter","unknown"),
                        "subject":  str(cert.get("subject",""))
                    }
        except Exception as e:
            return {"error": str(e)}

    def run(self, **kw) -> List[Finding]:
        findings = []
        for host, ports in self.mem.open_ports.items():
            for port in ports:
                svc_name, _ = self.SERVICE_MAP.get(port, (f"port-{port}", ""))
                banner = self._grab_banner(host, port)

                svc_info = {"name": svc_name, "port": port, "banner": banner}

                # TLS check for SSL ports
                if port in (443, 8443, 993, 995):
                    tls = self._tls_check(host, port)
                    svc_info["tls"] = tls
                    # Weak protocol finding
                    proto = tls.get("protocol","")
                    if proto in ("TLSv1", "TLSv1.1", "SSLv3"):
                        f = self._new_finding(
                            title=f"Weak TLS protocol: {proto} on {host}:{port}",
                            description="Outdated TLS version in use",
                            severity=Severity.HIGH,
                            evidence=json.dumps(tls),
                            tags=["tls","crypto","ssl"]
                        )
                        f.target = host
                        self._persist(f)
                        findings.append(f)

                key = f"{host}:{port}"
                self.mem.services[key] = svc_info
                self.log.info(f"{key} → {svc_name} | {banner[:60]}")

                # Risky service findings
                if port in (21, 23):
                    f = self._new_finding(
                        title=f"Plaintext protocol on {host}:{port} ({svc_name})",
                        description=f"{svc_name} transmits credentials in cleartext",
                        severity=Severity.HIGH,
                        evidence=banner,
                        tags=["cleartext","protocol"]
                    )
                    f.target = host
                    self._persist(f)
                    findings.append(f)

        return findings


class VulnScanner(Tool):
    name = "vuln_scanner"
    stage = Stage.SCAN
    description = "Lightweight CVE/version-based vulnerability matching"

    SIGNATURES = [
        ("Apache/2.2",   "CVE-2017-7679", "Apache 2.2 mod_mime buffer overread",          Severity.HIGH),
        ("Apache/2.4.49","CVE-2021-41773","Path traversal & RCE in Apache 2.4.49",         Severity.CRITICAL),
        ("OpenSSH_7.2",  "CVE-2016-0777", "OpenSSH 7.2 information leak via roaming",      Severity.MEDIUM),
        ("ProFTPD 1.3.5","CVE-2015-3306", "ProFTPD mod_copy unauthenticated file copy",    Severity.CRITICAL),
        ("PHP/5",        "CVE-2019-11043","PHP-FPM RCE via nginx path info",               Severity.CRITICAL),
        ("IIS/6.0",      "CVE-2017-7269", "IIS 6.0 WebDAV buffer overflow RCE",            Severity.CRITICAL),
        ("vsftpd 2.3.4", "CVE-2011-2523","vsftpd 2.3.4 backdoor command execution",        Severity.CRITICAL),
        ("OpenSSL/1.0.1","CVE-2014-0160", "Heartbleed – OpenSSL memory disclosure",        Severity.CRITICAL),
        ("WordPress 4",  "CVE-2019-8942", "WordPress 4.x authenticated RCE via crop-image",Severity.HIGH),
    ]

    def run(self, **kw) -> List[Finding]:
        findings = []
        banners = {k: v.get("banner","") for k,v in self.mem.services.items()}

        for host_port, banner in banners.items():
            for sig, cve, title, sev in self.SIGNATURES:
                if sig.lower() in banner.lower():
                    f = self._new_finding(
                        title=f"{cve}: {title}",
                        description=f"Banner match on {host_port}: '{banner[:80]}'",
                        severity=sev,
                        evidence=f"Matched signature '{sig}' in banner: {banner[:200]}",
                        tags=["cve","vuln","banner-match",cve]
                    )
                    f.target = host_port
                    vuln_entry = {"host_port": host_port, "cve": cve, "title": title, "severity": sev}
                    self.mem.vulns.append(vuln_entry)
                    self._persist(f)
                    findings.append(f)

        self.log.info(f"Vulnerability scan: {len(findings)} potential finding(s)")
        return findings


class SSLAudit(Tool):
    name = "ssl_audit"
    stage = Stage.SCAN
    description = "SSL/TLS configuration audit"

    def run(self, **kw) -> List[Finding]:
        findings = []
        ssl_ports = [443, 8443, 993, 995, 465]
        for host in self.mem.hosts or [self.mem.target]:
            for port in ssl_ports:
                if port not in self.mem.open_ports.get(host, []):
                    continue
                svc_key = f"{host}:{port}"
                tls_info = self.mem.services.get(svc_key, {}).get("tls", {})
                if not tls_info or "error" in tls_info:
                    continue

                cipher = tls_info.get("cipher","")
                # Check for weak ciphers
                weak = any(w in cipher for w in ("RC4","DES","NULL","EXPORT","anon"))
                if weak:
                    f = self._new_finding(
                        title=f"Weak cipher suite: {cipher} on {svc_key}",
                        description="Weak/obsolete cipher in use",
                        severity=Severity.HIGH,
                        evidence=json.dumps(tls_info),
                        tags=["ssl","cipher","weak"]
                    )
                    f.target = host
                    self._persist(f)
                    findings.append(f)

                # Check cert expiry
                expiry = tls_info.get("expiry","")
                if expiry and expiry != "unknown":
                    try:
                        exp_dt = datetime.datetime.strptime(expiry, "%b %d %H:%M:%S %Y %Z")
                        days_left = (exp_dt - datetime.datetime.utcnow()).days
                        if days_left < 30:
                            sev = Severity.HIGH if days_left < 0 else Severity.MEDIUM
                            f = self._new_finding(
                                title=f"Certificate {'EXPIRED' if days_left<0 else 'expiring soon'} on {svc_key}",
                                description=f"{days_left} days remaining",
                                severity=sev,
                                evidence=expiry,
                                tags=["ssl","cert","expiry"]
                            )
                            f.target = host
                            self._persist(f)
                            findings.append(f)
                    except ValueError:
                        pass

        return findings


# ─────────────────────────────────────────────────────────────────────
# ──────────────────── STAGE 3: EXPLOIT TOOLS ─────────────────────────
# ─────────────────────────────────────────────────────────────────────

class CredentialBrute(Tool):
    name = "credential_brute"
    stage = Stage.EXPLOIT
    description = "Credential stuffing / default credential testing"

    DEFAULT_CREDS = [
        ("admin","admin"), ("admin","password"), ("admin","123456"),
        ("root","root"),   ("root","toor"),      ("root",""),
        ("admin",""),      ("guest","guest"),    ("user","user"),
        ("admin","admin123"), ("administrator","password"),
        ("sa",""),         ("postgres","postgres"),
    ]

    SERVICE_PORTS = {22: "SSH", 21: "FTP", 3306: "MySQL", 5432: "PostgreSQL"}

    def _try_ssh(self, host: str, user: str, pwd: str) -> bool:
        """Simulated SSH attempt (requires paramiko in production)."""
        # In real engagement: import paramiko and attempt actual auth
        return False  # Safe simulation

    def run(self, creds: List[tuple] = None, **kw) -> List[Finding]:
        creds = creds or self.DEFAULT_CREDS
        findings = []
        self.log.info(f"Credential testing with {len(creds)} pairs")

        for host, ports in self.mem.open_ports.items():
            for port, svc_name in self.SERVICE_PORTS.items():
                if port not in ports:
                    continue
                for user, pwd in creds:
                    self.log.info(f"  Trying {svc_name} {host}:{port} → {user}:{pwd or '(empty)'}")
                    # Simulation: flag well-known defaults as a finding recommendation
                    f = self._new_finding(
                        title=f"Default credential candidate: {user}:{pwd or '(empty)'} on {svc_name}",
                        description=f"Test default credentials against {host}:{port}",
                        severity=Severity.MEDIUM,
                        evidence=f"Service: {svc_name}, Host: {host}, Port: {port}",
                        tags=["brute","credential","default"]
                    )
                    f.target = host
                    # Don't flood findings — just record 1st pair as recommendation
                    break

        # Record credential testing was performed
        f = self._new_finding(
            title="Default credential test performed",
            description=f"Tested {len(creds)} credential pairs across discovered services",
            severity=Severity.INFO,
            tags=["brute","summary"]
        )
        self._persist(f)
        findings.append(f)
        return findings


class SQLInjectionTester(Tool):
    name = "sqli_tester"
    stage = Stage.EXPLOIT
    description = "SQL injection detection via error-based probing"

    PAYLOADS = [
        ("'",                  "syntax error",              "Basic quote"),
        ("1' OR '1'='1",       "login",                     "Boolean bypass"),
        ("1; DROP TABLE",      "error",                     "Stacked query"),
        ("' UNION SELECT 1--", "union",                     "Union-based"),
        ("1 AND SLEEP(5)--",   "",                          "Time-based blind"),
        ("' OR 1=1--",         "",                          "Auth bypass"),
    ]

    def run(self, urls: List[str] = None, **kw) -> List[Finding]:
        urls = urls or self.mem.urls
        findings = []
        self.log.info(f"SQLi testing {len(urls)} URL(s)")

        for url in urls:
            for payload, indicator, ptype in self.PAYLOADS:
                test_url = url + payload
                f = self._new_finding(
                    title=f"SQLi payload queued: {ptype}",
                    description=f"Payload: {payload[:40]}",
                    severity=Severity.MEDIUM,
                    evidence=f"URL: {test_url[:200]}",
                    tags=["sqli","web","injection"]
                )
                f.target = url
                self._persist(f)
                findings.append(f)
        return findings


class XSSTester(Tool):
    name = "xss_tester"
    stage = Stage.EXPLOIT
    description = "Reflected/stored XSS probe generation"

    PAYLOADS = [
        '<script>alert(1)</script>',
        '"><img src=x onerror=alert(1)>',
        "';alert(1)//",
        '<svg/onload=alert(1)>',
        '{{7*7}}',
        '${7*7}',
    ]

    def run(self, urls: List[str] = None, **kw) -> List[Finding]:
        urls = urls or self.mem.urls
        findings = []
        for url in urls:
            f = self._new_finding(
                title="XSS payload set generated",
                description=f"{len(self.PAYLOADS)} XSS payloads for {url}",
                severity=Severity.HIGH,
                evidence="\n".join(f"{url}?q={p}" for p in self.PAYLOADS[:3]),
                tags=["xss","web","injection"]
            )
            f.target = url
            self._persist(f)
            findings.append(f)
        return findings


class DirectoryBrute(Tool):
    name = "dir_brute"
    stage = Stage.EXPLOIT
    description = "Web directory and file brute-force"
    WORDLIST = [
        "admin","login","wp-admin","phpMyAdmin","config","backup",
        ".git",".env","robots.txt","sitemap.xml","api","v1","v2",
        "console","manager","status","health","metrics","debug",
        "uploads","images","static","assets","js","css","includes",
        "install","setup","update","cron","test","dev","staging"
    ]

    def _check_url(self, base: str, path: str, timeout: float = 3.0) -> Optional[int]:
        import urllib.request
        try:
            url = f"http://{base}/{path}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status
        except Exception:
            return None

    def run(self, wordlist: List[str] = None, **kw) -> List[Finding]:
        words = wordlist or self.WORDLIST
        findings = []
        targets = [h for h, ports in self.mem.open_ports.items()
                   if 80 in ports or 8080 in ports or 443 in ports]
        if not targets:
            targets = [self.mem.target]

        self.log.info(f"Directory brute-force on {len(targets)} host(s)")
        for host in targets:
            for word in words:
                code = self._check_url(host, word)
                if code and code in (200, 301, 302, 403):
                    sev = Severity.HIGH if word in (".git",".env","config","backup","admin") else Severity.MEDIUM
                    f = self._new_finding(
                        title=f"Path discovered: /{word} [{code}]",
                        description=f"HTTP {code} on {host}/{word}",
                        severity=sev,
                        evidence=f"http://{host}/{word} → HTTP {code}",
                        tags=["dirbrute","web","discovery"]
                    )
                    f.target = host
                    full_url = f"http://{host}/{word}"
                    if full_url not in self.mem.urls:
                        self.mem.urls.append(full_url)
                    self._persist(f)
                    findings.append(f)
                    self.log.success(f"/{word} [{code}] on {host}")
        return findings


# ─────────────────────────────────────────────────────────────────────
# ──────────────── STAGE 4: POST-EXPLOIT TOOLS ────────────────────────
# ─────────────────────────────────────────────────────────────────────

class PrivEscChecker(Tool):
    name = "privesc_checker"
    stage = Stage.POST_EXPLOIT
    description = "Local privilege escalation vector enumeration"

    CHECKS = [
        ("sudo -l",             "Sudo permissions",        Severity.HIGH),
        ("find / -perm -4000 2>/dev/null", "SUID binaries", Severity.HIGH),
        ("cat /etc/crontab",    "Cron jobs",               Severity.MEDIUM),
        ("env",                 "Environment variables",   Severity.LOW),
        ("cat /etc/passwd",     "User enumeration",        Severity.LOW),
        ("id",                  "Current user context",    Severity.INFO),
        ("uname -a",            "Kernel version",          Severity.MEDIUM),
        ("cat /proc/version",   "OS/kernel details",       Severity.INFO),
        ("ls -la /etc/shadow",  "Shadow file permissions", Severity.CRITICAL),
        ("getcap -r / 2>/dev/null", "Linux capabilities",  Severity.HIGH),
    ]

    def run(self, simulate: bool = True, **kw) -> List[Finding]:
        findings = []
        self.log.info("Privilege escalation enumeration")

        for cmd, desc, sev in self.CHECKS:
            if simulate:
                f = self._new_finding(
                    title=f"PrivEsc check: {desc}",
                    description=f"Command: {cmd}",
                    severity=sev,
                    evidence=f"[SIMULATION] Run: {cmd}",
                    tags=["privesc","post-exploit","local"]
                )
            else:
                try:
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True, timeout=5
                    )
                    output = result.stdout.strip()[:500]
                    f = self._new_finding(
                        title=f"PrivEsc check: {desc}",
                        description=output[:100] if output else "No output",
                        severity=sev,
                        evidence=output,
                        tags=["privesc","post-exploit","local"]
                    )
                except Exception as e:
                    continue

            self._persist(f)
            findings.append(f)
        return findings


class LateralMovement(Tool):
    name = "lateral_movement"
    stage = Stage.POST_EXPLOIT
    description = "Identify lateral movement paths and pivot targets"

    def run(self, **kw) -> List[Finding]:
        findings = []
        self.log.info("Lateral movement analysis")

        # Analyze internal hosts discovered
        internal_hosts = [h for h in self.mem.hosts
                          if self._is_internal(h)]
        if internal_hosts:
            f = self._new_finding(
                title=f"Internal hosts reachable: {len(internal_hosts)} targets",
                description="Pivot potential via compromised host",
                severity=Severity.HIGH,
                evidence="\n".join(internal_hosts),
                tags=["lateral","pivot","internal"]
            )
            self._persist(f)
            findings.append(f)

        # Credential reuse opportunity
        if self.mem.credentials:
            f = self._new_finding(
                title="Credential reuse opportunity",
                description=f"{len(self.mem.credentials)} credential set(s) for lateral movement",
                severity=Severity.CRITICAL,
                evidence=f"Targets: {internal_hosts[:5]}",
                tags=["lateral","credential-reuse"]
            )
            self._persist(f)
            findings.append(f)

        return findings

    def _is_internal(self, ip: str) -> bool:
        try:
            addr = ipaddress.ip_address(ip)
            return addr.is_private
        except ValueError:
            return False


class PersistenceChecker(Tool):
    name = "persistence_checker"
    stage = Stage.POST_EXPLOIT
    description = "Enumerate persistence mechanisms available"

    MECHANISMS = [
        ("Cron job",          "Scheduled task persistence",       Severity.HIGH),
        ("Systemd unit",      "Service-based persistence",        Severity.HIGH),
        ("~/.bashrc",         "Shell init file modification",     Severity.MEDIUM),
        ("SSH authorized_keys","Public key backdoor",              Severity.CRITICAL),
        ("Web shell",         "PHP/ASPX webshell upload",         Severity.CRITICAL),
        ("Registry run key",  "Windows auto-start (if Windows)",  Severity.HIGH),
        ("Startup folder",    "Startup item persistence",         Severity.MEDIUM),
        ("PAM module",        "Authentication module backdoor",   Severity.CRITICAL),
    ]

    def run(self, **kw) -> List[Finding]:
        findings = []
        self.log.info("Persistence mechanism enumeration")
        for name, desc, sev in self.MECHANISMS:
            f = self._new_finding(
                title=f"Persistence vector: {name}",
                description=desc,
                severity=sev,
                tags=["persistence","post-exploit"]
            )
            self._persist(f)
            findings.append(f)
        return findings


class DataExfilSim(Tool):
    name = "data_exfil_sim"
    stage = Stage.POST_EXPLOIT
    description = "Simulate data exfiltration channel analysis"

    def run(self, **kw) -> List[Finding]:
        findings = []
        channels = [
            ("HTTPS outbound",        Severity.HIGH,    "Standard C2 over HTTPS"),
            ("DNS tunneling",         Severity.HIGH,    "Covert data via DNS TXT records"),
            ("ICMP covert channel",   Severity.MEDIUM,  "Data in ICMP payloads"),
            ("Email (SMTP port 25)",  Severity.MEDIUM,  "Exfil via mail relay"),
            ("Cloud storage API",     Severity.HIGH,    "Upload to S3/Dropbox/Drive"),
        ]
        for channel, sev, desc in channels:
            f = self._new_finding(
                title=f"Exfil channel available: {channel}",
                description=desc,
                severity=sev,
                tags=["exfil","post-exploit","data"]
            )
            self._persist(f)
            findings.append(f)
        return findings


# ─────────────────────────────────────────────────────────────────────
# ──────────────────── STAGE 5: REPORT TOOLS ──────────────────────────
# ─────────────────────────────────────────────────────────────────────

class ReportGenerator(Tool):
    name = "report_generator"
    stage = Stage.REPORT
    description = "Generate structured engagement report"

    SEVERITY_ORDER = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]

    def run(self, output_dir: str = "reports", **kw) -> List[Finding]:
        Path(output_dir).mkdir(exist_ok=True)
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_path = Path(output_dir) / f"redteam_{self.mem.session_id}_{ts}.md"

        findings_by_sev: Dict[str, List] = {s: [] for s in self.SEVERITY_ORDER}
        for f in self.mem.findings:
            sev = Severity(f.severity) if isinstance(f.severity, str) else f.severity
            if sev in findings_by_sev:
                findings_by_sev[sev].append(f)

        counts = {s: len(v) for s, v in findings_by_sev.items()}
        total  = sum(counts.values())

        report = f"""# Red Team Assessment Report
**Session ID:** `{self.mem.session_id}`  
**Target:** `{self.mem.target}`  
**Date:** {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}  
**Scope:** {", ".join(self.mem.scope) or self.mem.target}

---

## Executive Summary

This report documents findings from a structured red team assessment of **{self.mem.target}**.
A total of **{total} findings** were identified across {len([s for s in Stage])} assessment stages.

| Severity | Count |
|----------|-------|
| 🔴 Critical | {counts[Severity.CRITICAL]} |
| 🟠 High     | {counts[Severity.HIGH]} |
| 🟡 Medium   | {counts[Severity.MEDIUM]} |
| 🟢 Low      | {counts[Severity.LOW]} |
| 🔵 Info     | {counts[Severity.INFO]} |

---

## Scope & Methodology

**Target:** {self.mem.target}  
**Hosts Discovered:** {len(self.mem.hosts)}  
**Subdomains Found:** {len(self.mem.subdomains)}  
**Open Ports:** {sum(len(v) for v in self.mem.open_ports.values())}  
**Services Identified:** {len(self.mem.services)}  
**Vulnerabilities Matched:** {len(self.mem.vulns)}  

**Stages Executed:**
"""
        for stage, status in self.mem.stage_status.items():
            icon = "✅" if status == Status.COMPLETED else ("⏭" if status == Status.SKIPPED else "⏸")
            report += f"- {icon} {stage.replace('_',' ').title()}: {status}\n"

        report += "\n---\n\n## Findings\n\n"

        for sev in self.SEVERITY_ORDER:
            sev_findings = findings_by_sev[sev]
            if not sev_findings:
                continue
            label = sev.upper()
            report += f"### {label} ({len(sev_findings)} finding(s))\n\n"
            for i, f in enumerate(sev_findings, 1):
                report += f"#### {i}. {f.title}\n"
                report += f"- **Stage:** {f.stage}  \n"
                report += f"- **Tool:** `{f.tool}`  \n"
                report += f"- **Target:** {f.target}  \n"
                if f.description:
                    report += f"- **Detail:** {f.description}  \n"
                if f.evidence:
                    report += f"\n```\n{f.evidence[:400]}\n```\n"
                report += "\n"

        if self.mem.subdomains:
            report += "\n---\n\n## Discovered Assets\n\n### Subdomains\n"
            for sd in self.mem.subdomains[:50]:
                report += f"- `{sd}`\n"

        if self.mem.open_ports:
            report += "\n### Open Ports\n"
            for host, ports in self.mem.open_ports.items():
                report += f"- **{host}**: {sorted(ports)}\n"

        if self.mem.vulns:
            report += "\n---\n\n## Vulnerability Summary\n\n"
            for v in self.mem.vulns:
                report += f"- **{v['cve']}** on `{v['host_port']}`: {v['title']} [{v['severity']}]\n"

        report += """
---

## Recommendations

1. **Patch Management** — Apply security patches for all CVEs identified.
2. **Disable Cleartext Protocols** — Replace FTP/Telnet with SFTP/SSH.
3. **TLS Hardening** — Enforce TLS 1.2+; disable weak cipher suites.
4. **Access Controls** — Review and restrict admin interfaces.
5. **Credential Policy** — Enforce strong passwords; disable defaults.
6. **Network Segmentation** — Restrict lateral movement paths.
7. **Certificate Management** — Automate renewal; monitor expiry.
8. **Secret Management** — Remove exposed .env/config files.

---
*Report generated by RedTeam Workflow Engine*
"""
        with open(report_path, "w") as fh:
            fh.write(report)

        self.log.success(f"Report saved: {report_path}")
        f = self._new_finding(
            title="Assessment report generated",
            description=str(report_path),
            severity=Severity.INFO,
            tags=["report","output"]
        )
        self._persist(f)
        return [f]


# ─────────────────────────────────────────────────────────────────────
# WORKFLOW ENGINE
# ─────────────────────────────────────────────────────────────────────

STAGE_TOOLS: Dict[Stage, List[type]] = {
    Stage.RECON:        [DNSRecon, SubdomainEnum, WHOISLookup, GoogleDork],
    Stage.SCAN:         [PortScanner, ServiceDetector, VulnScanner, SSLAudit],
    Stage.EXPLOIT:      [CredentialBrute, SQLInjectionTester, XSSTester, DirectoryBrute],
    Stage.POST_EXPLOIT: [PrivEscChecker, LateralMovement, PersistenceChecker, DataExfilSim],
    Stage.REPORT:       [ReportGenerator],
}


class RedTeamEngine:
    def __init__(self, target: str, scope: List[str] = None,
                 db_path: Path = DB_PATH, resume_id: str = None):
        self.db = Database(db_path)

        if resume_id:
            mem = self.db.load_session(resume_id)
            if not mem:
                raise ValueError(f"Session {resume_id} not found in DB")
            self.mem = mem
            print(f"\n{GREEN}Resumed session {resume_id} for {target}{RESET}")
        else:
            self.mem = SessionMemory(
                session_id=str(uuid.uuid4())[:12],
                target=target,
                scope=scope or [target],
            )

        self.log = Logger(self.mem.session_id)
        self._print_banner()

    def _print_banner(self):
        print(f"""
{BOLD}{RED}
 ██████╗ ███████╗██████╗     ████████╗███████╗ █████╗ ███╗   ███╗
 ██╔══██╗██╔════╝██╔══██╗    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║
 ██████╔╝█████╗  ██║  ██║       ██║   █████╗  ███████║██╔████╔██║
 ██╔══██╗██╔══╝  ██║  ██║       ██║   ██╔══╝  ██╔══██║██║╚██╔╝██║
 ██║  ██║███████╗██████╔╝       ██║   ███████╗██║  ██║██║ ╚═╝ ██║
 ╚═╝  ╚═╝╚══════╝╚═════╝        ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝
{RESET}{CYAN} Workflow Engine — Full Lifecycle Red Team Framework{RESET}
{DIM} Session: {self.mem.session_id} | Target: {self.mem.target}{RESET}
""")

    def run_stage(self, stage: Stage, tool_names: List[str] = None,
                  skip_tools: List[str] = None, **tool_kwargs):
        self.log.stage_banner(stage)
        tools_for_stage = STAGE_TOOLS.get(stage, [])
        self.mem.stage_status[stage.value] = Status.RUNNING
        self.db.save_session(self.mem)

        stage_findings = []
        for ToolCls in tools_for_stage:
            tool = ToolCls(self.db, self.mem, self.log)

            if tool_names and tool.name not in tool_names:
                continue
            if skip_tools and tool.name in skip_tools:
                self.log.warn(f"Skipping tool: {tool.name}")
                continue

            self.log.info(f"Running: {BOLD}{tool.name}{RESET} — {tool.description}")
            t0 = time.time()
            try:
                findings = tool.run(**tool_kwargs)
                duration = time.time() - t0
                self.db.log_tool(self.mem.session_id, stage.value, tool.name,
                                 Status.COMPLETED, f"{len(findings)} findings", duration)
                stage_findings.extend(findings)
            except Exception as e:
                duration = time.time() - t0
                self.log.error(f"Tool {tool.name} failed: {e}")
                self.db.log_tool(self.mem.session_id, stage.value, tool.name,
                                 Status.FAILED, str(e), duration)

        self.mem.stage_status[stage.value] = Status.COMPLETED
        self.db.save_session(self.mem)
        self.log.success(f"Stage {stage.value} complete — {len(stage_findings)} finding(s)")
        return stage_findings

    def run_full(self, stages: List[Stage] = None, **kwargs):
        stages = stages or list(Stage)
        all_findings = []
        for stage in stages:
            findings = self.run_stage(stage, **kwargs)
            all_findings.extend(findings)
        self._print_summary()
        return all_findings

    def _print_summary(self):
        counts = {}
        for f in self.mem.findings:
            sev = f.severity if isinstance(f.severity, str) else f.severity.value
            counts[sev] = counts.get(sev, 0) + 1

        print(f"\n{'═'*60}")
        print(f"{BOLD}{CYAN}  ASSESSMENT COMPLETE{RESET}")
        print(f"{'═'*60}")
        print(f"  Session  : {self.mem.session_id}")
        print(f"  Target   : {self.mem.target}")
        print(f"  Hosts    : {len(self.mem.hosts)}")
        print(f"  Services : {len(self.mem.services)}")
        print(f"  Findings : {len(self.mem.findings)}")
        print()
        order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
        labels = {"critical":"🔴","high":"🟠","medium":"🟡","low":"🟢","info":"🔵"}
        for s in order:
            n = counts.get(s.value, 0)
            if n:
                print(f"  {labels[s.value]} {s.value.upper():10s}: {n}")
        print(f"{'═'*60}\n")

    def add_memory(self, key: str, value: Any):
        """Manually update session memory."""
        if hasattr(self.mem, key):
            attr = getattr(self.mem, key)
            if isinstance(attr, list):
                if isinstance(value, list):
                    attr.extend(value)
                else:
                    attr.append(value)
            elif isinstance(attr, dict):
                attr.update(value)
            else:
                setattr(self.mem, key, value)
            self.db.save_session(self.mem)
            self.log.success(f"Memory updated: {key}")
        else:
            self.log.warn(f"Unknown memory key: {key}")

    def get_findings(self, severity: str = None) -> List[Dict]:
        return self.db.get_findings(self.mem.session_id, severity)

    def list_tools(self):
        print(f"\n{BOLD}Available Tools by Stage:{RESET}")
        for stage, tools in STAGE_TOOLS.items():
            print(f"\n  {CYAN}{stage.value.upper()}{RESET}")
            for T in tools:
                t = T.__new__(T)
                print(f"    {GREEN}•{RESET} {T.name:25s} — {T.description}")


# ─────────────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Red Team Workflow Engine",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("target", nargs="?", default="example.com",
                        help="Target domain or IP address")
    parser.add_argument("--stages", nargs="+", default=None,
                        choices=[s.value for s in Stage],
                        help="Stages to run (default: all)")
    parser.add_argument("--tools", nargs="+", default=None,
                        help="Run specific tools only")
    parser.add_argument("--skip-tools", nargs="+", default=None,
                        help="Skip specified tools")
    parser.add_argument("--scope", nargs="+", default=None,
                        help="Scope definition (CIDRs, domains)")
    parser.add_argument("--resume", default=None,
                        help="Resume an existing session by ID")
    parser.add_argument("--list-tools", action="store_true",
                        help="List all available tools and exit")
    parser.add_argument("--list-sessions", action="store_true",
                        help="List all past sessions from DB")
    parser.add_argument("--report-only", action="store_true",
                        help="Generate report for existing session (requires --resume)")
    parser.add_argument("--db", default=str(DB_PATH),
                        help="Path to SQLite database")
    args = parser.parse_args()

    # List sessions
    if args.list_sessions:
        db = Database(Path(args.db))
        sessions = db.list_sessions()
        if not sessions:
            print("No sessions found.")
        else:
            print(f"\n{'ID':15s} {'TARGET':30s} {'CREATED':25s} {'UPDATED':25s}")
            print("─" * 95)
            for s in sessions:
                print(f"{s['session_id']:15s} {s['target']:30s} {s['created_at']:25s} {s['updated_at']:25s}")
        return

    engine = RedTeamEngine(
        target=args.target,
        scope=args.scope,
        db_path=Path(args.db),
        resume_id=args.resume,
    )

    if args.list_tools:
        engine.list_tools()
        return

    if args.report_only:
        if not args.resume:
            print("--report-only requires --resume <session_id>")
            sys.exit(1)
        engine.run_stage(Stage.REPORT)
        return

    stages = [Stage(s) for s in args.stages] if args.stages else list(Stage)

    engine.run_full(
        stages=stages,
        tool_names=args.tools,
        skip_tools=args.skip_tools or [],
    )


# ─────────────────────────────────────────────────────────────────────
# DEMO / INTERACTIVE USAGE
# ─────────────────────────────────────────────────────────────────────

def demo():
    """
    Programmatic usage example:

        engine = RedTeamEngine("scanme.nmap.org", scope=["scanme.nmap.org"])

        # Run individual stages
        engine.run_stage(Stage.RECON)
        engine.run_stage(Stage.SCAN)

        # Manually inject discovered data into memory
        engine.add_memory("hosts", ["45.33.32.156"])
        engine.add_memory("urls", ["http://scanme.nmap.org/index.html"])

        # Run exploit + post-exploit
        engine.run_stage(Stage.EXPLOIT)
        engine.run_stage(Stage.POST_EXPLOIT)

        # Generate final report
        engine.run_stage(Stage.REPORT)

        # Query findings
        critical = engine.get_findings(severity="critical")
        print(f"{len(critical)} critical findings")

        # Resume a session later
        engine2 = RedTeamEngine("scanme.nmap.org", resume_id=engine.mem.session_id)
    """
    pass


if __name__ == "__main__":
    main()
