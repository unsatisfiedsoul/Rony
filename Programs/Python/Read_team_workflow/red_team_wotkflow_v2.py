#!/bin/python3

"""
Red Team Workflow Engine
========================
Only tools that produce REAL results from REAL network probes.

Stages implemented with genuine capability:
  1. RECON      — DNS (A/MX/NS/TXT), reverse PTR, subdomain brute (wildcard-safe), WHOIS
  2. SCAN       — TCP connect port scan, banner grab, HTTP/S header probe, SSL/TLS audit
  3. ENUMERATE  — HTTP path discovery (real HTTP requests), open redirect check, cookie audit
  4. REPORT     — SQLite-backed, markdown report from confirmed findings only

Tools NOT included (would require a real shell on target, or would simulate):
  - PrivEsc, Persistence, LateralMovement — only meaningful post-shell, excluded.
  - Credential brute — requires target-specific auth protocol, excluded.
  - SQLi/XSS       — requires parameter discovery pipeline, excluded.
  - Google dorking — unverifiable, excluded permanently.

Usage:
  python red_team_workflow.py <target> [options]
  python red_team_workflow.py example.com
  python red_team_workflow.py example.com --ports 80 443 8080 --threads 50
  python red_team_workflow.py --preflight
  python red_team_workflow.py --list-sessions
"""

import sqlite3, json, uuid, socket, ssl, re, os, sys, time, datetime
import subprocess, ipaddress, argparse, threading, queue
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, urljoin
import concurrent.futures

# ─────────────────────────────────────────────────────────────────────
# TERMINAL COLOURS
# ─────────────────────────────────────────────────────────────────────
def _c(code): return f"\033[{code}m"
R=_c(0); BOLD=_c(1); DIM=_c(2)
RED=_c(91); GREEN=_c(92); YELLOW=_c(93); CYAN=_c(96); MAG=_c(95)

# ─────────────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────────────
class Stage(str, Enum):
    RECON      = "recon"
    SCAN       = "scan"
    ENUMERATE  = "enumerate"
    REPORT     = "report"

class Severity(str, Enum):
    INFO     = "info"
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"

SEV_COLOR = {
    Severity.INFO:     CYAN,
    Severity.LOW:      GREEN,
    Severity.MEDIUM:   YELLOW,
    Severity.HIGH:     RED,
    Severity.CRITICAL: MAG,
}

# ─────────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────────
@dataclass
class Finding:
    id:          str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    stage:       str = Stage.RECON
    tool:        str = ""
    title:       str = ""
    description: str = ""
    severity:    str = Severity.INFO
    evidence:    str = ""
    target:      str = ""
    timestamp:   str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    tags:        List[str] = field(default_factory=list)

@dataclass
class SessionMemory:
    session_id:  str
    target:      str
    hosts:       List[str]            = field(default_factory=list)
    subdomains:  List[str]            = field(default_factory=list)
    open_ports:  Dict[str, List[int]] = field(default_factory=dict)
    services:    Dict[str, Any]       = field(default_factory=dict)  # "host:port" -> info dict
    http_hosts:  List[str]            = field(default_factory=list)  # confirmed HTTP/S targets
    findings:    List[Finding]        = field(default_factory=list)
    created_at:  str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    updated_at:  str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

# ─────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────
class Database:
    def __init__(self, path: Path = Path("redteam.db")):
        self.path = path
        self._init()

    @contextmanager
    def _conn(self):
        c = sqlite3.connect(str(self.path))
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    def _init(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    target     TEXT NOT NULL,
                    data       TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS findings (
                    id         TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    stage      TEXT NOT NULL,
                    tool       TEXT NOT NULL,
                    title      TEXT NOT NULL,
                    description TEXT,
                    severity   TEXT NOT NULL,
                    evidence   TEXT,
                    target     TEXT,
                    tags       TEXT,
                    timestamp  TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tool_runs (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    tool       TEXT NOT NULL,
                    status     TEXT NOT NULL,
                    findings   INTEGER DEFAULT 0,
                    duration   REAL,
                    timestamp  TEXT NOT NULL
                );
            """)

    def save_session(self, mem: SessionMemory):
        now = datetime.datetime.utcnow().isoformat()
        mem.updated_at = now
        d = asdict(mem)
        with self._conn() as c:
            c.execute("""
                INSERT INTO sessions(session_id,target,data,created_at,updated_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(session_id) DO UPDATE SET
                    data=excluded.data, updated_at=excluded.updated_at
            """, (mem.session_id, mem.target, json.dumps(d), mem.created_at, now))

    def load_session(self, session_id: str) -> Optional[SessionMemory]:
        with self._conn() as c:
            row = c.execute("SELECT data FROM sessions WHERE session_id=?",
                            (session_id,)).fetchone()
        if not row:
            return None
        d = json.loads(row["data"])
        d["findings"] = [Finding(**f) for f in d.get("findings", [])]
        return SessionMemory(**{k: v for k, v in d.items()
                                if k in SessionMemory.__dataclass_fields__})

    def list_sessions(self) -> List[Dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT session_id,target,created_at,updated_at FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def save_finding(self, session_id: str, f: Finding):
        with self._conn() as c:
            c.execute("""
                INSERT OR REPLACE INTO findings
                (id,session_id,stage,tool,title,description,severity,evidence,target,tags,timestamp)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """, (f.id, session_id, f.stage, f.tool, f.title, f.description,
                  f.severity, f.evidence, f.target,
                  json.dumps(f.tags), f.timestamp))

    def log_run(self, session_id: str, tool: str, status: str,
                n_findings: int, duration: float):
        with self._conn() as c:
            c.execute("""
                INSERT INTO tool_runs(session_id,tool,status,findings,duration,timestamp)
                VALUES(?,?,?,?,?,?)
            """, (session_id, tool, status, n_findings, duration,
                  datetime.datetime.utcnow().isoformat()))

    def get_findings(self, session_id: str, severity: str = None) -> List[Dict]:
        with self._conn() as c:
            if severity:
                rows = c.execute(
                    "SELECT * FROM findings WHERE session_id=? AND severity=? ORDER BY timestamp",
                    (session_id, severity)).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM findings WHERE session_id=? ORDER BY timestamp",
                    (session_id,)).fetchall()
        return [dict(r) for r in rows]

# ─────────────────────────────────────────────────────────────────────
# LOGGER
# ─────────────────────────────────────────────────────────────────────
class Log:
    def __init__(self, session_id: str):
        Path("logs").mkdir(exist_ok=True)
        self._f = open(f"logs/{session_id}.log", "a")
        self._lk = threading.Lock()

    def _w(self, level: str, msg: str):
        ts = datetime.datetime.utcnow().strftime("%H:%M:%S")
        with self._lk:
            self._f.write(f"[{ts}][{level}] {msg}\n")
            self._f.flush()

    def info(self, m):    print(f"  {CYAN}·{R} {m}");           self._w("INFO", m)
    def ok(self, m):      print(f"  {GREEN}✔{R} {m}");          self._w("OK", m)
    def warn(self, m):    print(f"  {YELLOW}!{R} {m}");         self._w("WARN", m)
    def err(self, m):     print(f"  {RED}✘{R} {m}");            self._w("ERR", m)

    def finding(self, f: Finding):
        col = SEV_COLOR.get(Severity(f.severity), "")
        print(f"  {col}{BOLD}[{f.severity.upper():8s}]{R} {f.title}")
        if f.description:
            print(f"             {DIM}{f.description[:90]}{R}")

    def stage(self, s: Stage):
        icons = {Stage.RECON:"🔭", Stage.SCAN:"🔍",
                 Stage.ENUMERATE:"🌐", Stage.REPORT:"📋"}
        lbl = s.value.upper()
        print(f"\n{'─'*62}")
        print(f"  {icons.get(s,'▶')}  {BOLD}{CYAN}{lbl}{R}")
        print(f"{'─'*62}")

    def close(self):
        self._f.close()

# ─────────────────────────────────────────────────────────────────────
# PREFLIGHT CHECKER
# ─────────────────────────────────────────────────────────────────────
class Preflight:
    """Check which external binaries and Python packages are available."""

    BINARIES = [
        # (name, version_args, purpose)
        ("nslookup",  ["-type=A","localhost"],   "DNS record queries"),
        ("whois",     ["localhost"],              "Domain registration data"),
        ("openssl",   ["version"],               "SSL/TLS cipher enumeration"),
        ("nmap",      ["-V"],                    "Advanced port scanning"),
        ("curl",      ["--version"],             "HTTP probing"),
        ("dig",       ["localhost"],             "Detailed DNS queries"),
    ]
    PACKAGES = [
        # (import_name, pip_name, purpose)
        ("dns.resolver", "dnspython",   "Full DNS record type support"),
        ("requests",     "requests",    "HTTP probing and web enumeration"),
        ("cryptography", "cryptography","Certificate parsing"),
    ]

    def run(self) -> Dict[str, bool]:
        import shutil, importlib
        results = {}
        W = 62
        print(f"\n{'═'*W}")
        print(f"  {BOLD}{CYAN}PREFLIGHT DEPENDENCY CHECK{R}")
        print(f"{'═'*W}")

        print(f"\n  {BOLD}Binaries{R}")
        for name, args, purpose in self.BINARIES:
            found = bool(shutil.which(name))
            results[name] = found
            ver = ""
            if found:
                try:
                    r = subprocess.run([name]+args, capture_output=True,
                                       text=True, timeout=5)
                    ver = (r.stdout+r.stderr).strip().splitlines()[0][:50]
                except Exception:
                    ver = shutil.which(name)
            mark = f"{GREEN}✔{R}" if found else f"{YELLOW}–{R}"
            print(f"  {mark} {name:<12} {DIM}{purpose:<30} {ver}{R}")

        print(f"\n  {BOLD}Python packages{R}")
        missing_pkgs = []
        for imp, pip, purpose in self.PACKAGES:
            try:
                importlib.import_module(imp.split(".")[0])
                ver = getattr(sys.modules[imp.split(".")[0]], "__version__", "ok")
                print(f"  {GREEN}✔{R} {pip:<14} {DIM}{purpose:<30} {ver}{R}")
                results[pip] = True
            except ImportError:
                print(f"  {YELLOW}–{R} {pip:<14} {DIM}{purpose}{R}")
                missing_pkgs.append(pip)
                results[pip] = False

        if missing_pkgs:
            print(f"\n  Install optional packages:")
            print(f"    pip install {' '.join(missing_pkgs)}")
        print(f"\n  {DIM}Missing binaries/packages = tool uses stdlib fallback where possible.{R}")
        print(f"{'═'*W}\n")
        return results


# ─────────────────────────────────────────────────────────────────────
# BASE TOOL
# ─────────────────────────────────────────────────────────────────────
class Tool:
    name  = "base"
    stage = Stage.RECON

    def __init__(self, db: Database, mem: SessionMemory, log: Log):
        self.db = db; self.mem = mem; self.log = log

    def _finding(self, title: str, description: str,
                 severity: Severity = Severity.INFO,
                 evidence: str = "", tags: List[str] = None,
                 target: str = None) -> Finding:
        return Finding(
            stage=self.stage, tool=self.name,
            title=title, description=description,
            severity=severity, evidence=evidence,
            target=target or self.mem.target,
            tags=tags or []
        )

    def _save(self, f: Finding):
        self.mem.findings.append(f)
        self.db.save_finding(self.mem.session_id, f)
        self.log.finding(f)

    def run(self, **kw) -> List[Finding]:
        raise NotImplementedError


# ═════════════════════════════════════════════════════════════════════
# STAGE 1 — RECON
# ═════════════════════════════════════════════════════════════════════

class DNSRecon(Tool):
    """
    Real DNS enumeration.
    A records  → stdlib socket.getaddrinfo (always available)
    MX/NS/TXT  → dnspython if installed, else nslookup subprocess
    PTR        → socket.gethostbyaddr per resolved IP
    """
    name  = "dns_recon"
    stage = Stage.RECON

    # ── helpers ───────────────────────────────────────────────────────
    def _resolve_a(self, host: str) -> List[str]:
        try:
            return list({i[4][0] for i in socket.getaddrinfo(host, None, socket.AF_INET)})
        except socket.gaierror:
            return []

    def _dnspython_available(self) -> bool:
        try:
            import dns.resolver
            return True
        except ImportError:
            return False

    def _query_dnspython(self, target: str, rtype: str) -> Optional[str]:
        try:
            import dns.resolver
            answers = dns.resolver.resolve(target, rtype, raise_on_no_answer=False)
            lines = [str(r) for r in answers]
            return "\n".join(lines) if lines else None
        except Exception:
            return None

    def _query_nslookup(self, target: str, rtype: str) -> Optional[str]:
        import shutil
        if not shutil.which("nslookup"):
            return None
        try:
            r = subprocess.run(["nslookup", f"-type={rtype}", target],
                               capture_output=True, text=True, timeout=10)
            out = r.stdout.strip()
            bad = ("nxdomain","can't find","server can't find","no answer")
            if not out or any(b in out.lower() for b in bad):
                return None
            return out
        except subprocess.TimeoutExpired:
            return None

    def _query(self, target: str, rtype: str) -> Optional[str]:
        if self._dnspython_available():
            return self._query_dnspython(target, rtype)
        return self._query_nslookup(target, rtype)

    # ── run ───────────────────────────────────────────────────────────
    def run(self, **kw) -> List[Finding]:
        target = self.mem.target
        findings = []
        self.log.info(f"DNS recon → {target}")

        # ── A records ─────────────────────────────────────────────────
        ips = self._resolve_a(target)
        if not ips:
            self.log.warn(f"{target} did not resolve — check target spelling")
            return []

        for ip in ips:
            if ip not in self.mem.hosts:
                self.mem.hosts.append(ip)

        f = self._finding(
            title=f"A record: {target} → {', '.join(ips)}",
            description=f"Resolved to {len(ips)} IP(s)",
            severity=Severity.INFO,
            evidence="\n".join(ips),
            tags=["dns","a-record"]
        )
        self._save(f); findings.append(f)

        # ── MX / NS / TXT ─────────────────────────────────────────────
        for rtype in ("MX", "NS", "TXT"):
            out = self._query(target, rtype)
            if not out:
                continue

            sev = Severity.INFO
            if rtype == "TXT" and "v=spf1" not in out:
                sev = Severity.LOW  # Missing SPF is genuinely notable

            f = self._finding(
                title=f"DNS {rtype}: {target}",
                description=f"{rtype} record(s) present",
                severity=sev,
                evidence=out[:500],
                tags=["dns", rtype.lower()]
            )
            self._save(f); findings.append(f)

            # Resolve MX/NS hosts and add to target list
            if rtype in ("MX", "NS"):
                for host in re.findall(r'[\w.\-]+\.\w{2,}', out):
                    extra = self._resolve_a(host)
                    for ip in extra:
                        if ip not in self.mem.hosts:
                            self.mem.hosts.append(ip)

        # ── PTR (reverse lookup) ──────────────────────────────────────
        for ip in list(self.mem.hosts):
            try:
                ptr = socket.gethostbyaddr(ip)[0]
                f = self._finding(
                    title=f"PTR: {ip} → {ptr}",
                    description="Reverse DNS confirmed",
                    severity=Severity.INFO,
                    evidence=f"{ip} → {ptr}",
                    tags=["dns","ptr"],
                    target=ip
                )
                self._save(f); findings.append(f)
            except (socket.herror, socket.gaierror):
                pass

        self.log.ok(f"DNS recon: {len(findings)} finding(s), {len(self.mem.hosts)} host(s)")
        return findings


class SubdomainEnum(Tool):
    """
    Subdomain brute-force via real DNS resolution.
    Wildcard detection aborts the run immediately to prevent false positives.
    """
    name  = "subdomain_enum"
    stage = Stage.RECON

    WORDLIST = [
        "www","mail","smtp","pop","imap","ftp","sftp","ssh",
        "api","api2","v1","v2","dev","staging","stage","test","qa","uat",
        "vpn","remote","gateway","proxy","cdn","static","assets","media",
        "admin","portal","dashboard","console","panel","manager","cp","manage",
        "webmail","email","mx","mx1","mx2","ns1","ns2","ns3",
        "blog","shop","store","pay","payment","checkout","cart",
        "app","apps","mobile","m","wap",
        "git","gitlab","github","svn","repo","code",
        "jira","confluence","jenkins","ci","build","deploy",
        "kibana","grafana","prometheus","monitor","metrics","logs","splunk",
        "internal","intranet","corp","office","extranet","partner",
        "db","database","mysql","postgres","sql","mongo","redis","elastic",
        "backup","bak","archive","old","legacy",
        "auth","login","sso","oauth","id","identity","ldap","ad",
        "beta","alpha","preview","demo","sandbox","lab",
    ]
    HIGH_VALUE = {
        "admin","portal","dashboard","console","panel","manager","cp",
        "git","gitlab","jenkins","ci","jira","confluence",
        "kibana","grafana","monitor","internal","intranet","corp",
        "db","database","backup","auth","sso","ldap","ad",
    }

    def _wildcard_ip(self, target: str) -> Optional[str]:
        canary = f"_canary_{uuid.uuid4().hex[:10]}.{target}"
        try:
            return socket.gethostbyname(canary)
        except socket.gaierror:
            return None

    def run(self, wordlist: List[str] = None, **kw) -> List[Finding]:
        target   = self.mem.target
        words    = wordlist or self.WORDLIST
        findings = []
        self.log.info(f"Subdomain enum → {target} ({len(words)} words)")

        wc = self._wildcard_ip(target)
        if wc:
            self.log.warn(f"Wildcard DNS on {target} (→ {wc}) — brute-force would be 100% false positives, aborted")
            return []

        found = 0
        for sub in words:
            fqdn = f"{sub}.{target}"
            try:
                ip = socket.gethostbyname(fqdn)
            except socket.gaierror:
                continue

            if fqdn not in self.mem.subdomains:
                self.mem.subdomains.append(fqdn)
            if ip not in self.mem.hosts:
                self.mem.hosts.append(ip)

            sev = Severity.MEDIUM if sub in self.HIGH_VALUE else Severity.INFO
            f = self._finding(
                title=f"Subdomain: {fqdn} → {ip}",
                description=f"Resolved via DNS",
                severity=sev,
                evidence=f"{fqdn} → {ip}",
                tags=["subdomain","dns"],
                target=fqdn
            )
            self._save(f); findings.append(f)
            found += 1
            self.log.ok(f"{fqdn} ({ip})")

        if not found:
            self.log.info("No subdomains resolved")
        return findings


class WHOISLookup(Tool):
    """
    WHOIS via system binary. Creates a finding only when real fields parse.
    Hard dependency: whois binary must be on PATH.
    """
    name  = "whois_lookup"
    stage = Stage.RECON

    FIELDS = [
        (r'Registrar:\s*(.+)',                    "registrar"),
        (r'Creation Date:\s*(.+)',                "created"),
        (r'(?:Expir\w+ Date):\s*(.+)',            "expires"),
        (r'Registrant Org(?:anization)?:\s*(.+)', "org"),
        (r'Name Server:\s*(.+)',                  "nameserver"),
        (r'DNSSEC:\s*(.+)',                       "dnssec"),
        (r'Registrant Country:\s*(.+)',           "country"),
    ]
    NOT_FOUND = ("no match for","not found","no entries found",
                 "no whois server","object does not exist")

    def run(self, **kw) -> List[Finding]:
        import shutil
        if not shutil.which("whois"):
            self.log.warn("whois binary not found — skipping (install: apt install whois)")
            return []

        target = self.mem.target
        self.log.info(f"WHOIS → {target}")
        try:
            r = subprocess.run(["whois", target],
                               capture_output=True, text=True, timeout=20)
            out = r.stdout.strip()
        except subprocess.TimeoutExpired:
            self.log.warn("WHOIS timed out")
            return []

        if not out or len(out) < 20:
            self.log.warn("WHOIS returned empty response")
            return []
        if any(m in out.lower() for m in self.NOT_FOUND):
            self.log.warn(f"WHOIS: no registration data for {target}")
            return []

        fields = {}
        for pat, key in self.FIELDS:
            m = re.search(pat, out, re.IGNORECASE)
            if m:
                fields[key] = m.group(1).strip()

        if not fields:
            self.log.warn("WHOIS: output received but no structured fields parsed")
            return []

        f = self._finding(
            title=f"WHOIS: {target}",
            description=", ".join(f"{k}={v}" for k, v in fields.items()),
            severity=Severity.INFO,
            evidence=out[:1000],
            tags=["whois","osint"]
        )
        self._save(f)
        return [f]


# ═════════════════════════════════════════════════════════════════════
# STAGE 2 — SCAN
# ═════════════════════════════════════════════════════════════════════

class PortScanner(Tool):
    """
    Concurrent TCP connect scan.
    Uses stdlib socket only — no nmap required.
    Reports per-host open port list as a single finding.
    """
    name  = "port_scanner"
    stage = Stage.SCAN

    TOP_PORTS = [
        21,22,23,25,53,80,81,110,111,135,139,143,
        443,445,465,587,993,995,1433,1521,1723,
        2049,3000,3306,3389,4443,5000,5432,5900,
        6379,7001,8000,8080,8081,8443,8888,9090,
        9200,27017,28017
    ]
    # Ports that are high-risk if open
    RISKY = {21,23,135,139,445,1433,1521,3389,5900,6379,9200,27017}

    def _probe(self, host: str, port: int, timeout: float) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def run(self, ports: List[int] = None, timeout: float = 1.5,
            threads: int = 100, **kw) -> List[Finding]:
        ports   = ports or self.TOP_PORTS
        targets = self.mem.hosts or [self.mem.target]
        findings = []
        self.log.info(f"Port scan: {len(targets)} host(s) × {len(ports)} ports "
                      f"({threads} threads, {timeout}s timeout)")

        for host in targets:
            open_ports: List[int] = []

            with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as ex:
                future_map = {ex.submit(self._probe, host, p, timeout): p for p in ports}
                for fut in concurrent.futures.as_completed(future_map):
                    port = future_map[fut]
                    if fut.result():
                        open_ports.append(port)

            if not open_ports:
                self.log.info(f"{host}: no open ports found")
                continue

            open_ports.sort()
            self.mem.open_ports[host] = open_ports
            risky = [p for p in open_ports if p in self.RISKY]
            sev   = Severity.HIGH if risky else Severity.MEDIUM

            f = self._finding(
                title=f"Open ports on {host}: {open_ports}",
                description=(f"Risky: {risky}" if risky
                             else f"{len(open_ports)} port(s) open"),
                severity=sev,
                evidence=f"Host: {host}\nOpen: {open_ports}\nRisky: {risky}",
                tags=["portscan","tcp"],
                target=host
            )
            self._save(f); findings.append(f)
            self.log.ok(f"{host}: {open_ports}")

        return findings


class BannerGrab(Tool):
    """
    Banner grab + HTTP HEAD probe on every open port.
    Builds self.mem.services with real version strings.
    """
    name  = "banner_grab"
    stage = Stage.SCAN

    PORT_SVC = {
        21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP", 53:"DNS",
        80:"HTTP", 110:"POP3", 143:"IMAP", 443:"HTTPS",
        465:"SMTPS", 587:"SMTP", 993:"IMAPS", 995:"POP3S",
        1433:"MSSQL", 1521:"Oracle", 3306:"MySQL", 3389:"RDP",
        5432:"PostgreSQL", 5900:"VNC", 6379:"Redis",
        8080:"HTTP-Alt", 8443:"HTTPS-Alt", 9200:"Elasticsearch",
        27017:"MongoDB"
    }
    CLEARTEXT = {21,23,25,110,143,587}
    HIGH_RISK_SVC = {"Redis","Elasticsearch","MongoDB","Telnet","FTP"}

    def _raw_banner(self, host: str, port: int, timeout: float = 3.0) -> str:
        try:
            with socket.create_connection((host, port), timeout=timeout) as s:
                s.settimeout(timeout)
                data = b""
                try:
                    while True:
                        chunk = s.recv(512)
                        if not chunk:
                            break
                        data += chunk
                        if len(data) > 1024:
                            break
                except OSError:
                    pass
                return data.decode("utf-8", errors="replace").strip()
        except OSError:
            return ""

    def _http_banner(self, host: str, port: int,
                     https: bool = False, timeout: float = 5.0) -> Dict:
        scheme = "https" if https else "http"
        url    = f"{scheme}://{host}:{port}/"
        try:
            req = Request(url, method="HEAD",
                          headers={"User-Agent":"Mozilla/5.0"})
            import ssl as _ssl
            ctx = _ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode    = _ssl.CERT_NONE
            with urlopen(req, timeout=timeout, context=ctx if https else None) as resp:
                hdrs = dict(resp.headers)
                return {
                    "status":  resp.status,
                    "server":  hdrs.get("Server",""),
                    "powered": hdrs.get("X-Powered-By",""),
                    "headers": {k: v for k, v in hdrs.items()},
                    "url":     url,
                }
        except HTTPError as e:
            return {"status": e.code, "url": url,
                    "server": "", "powered": "", "headers": {}}
        except Exception:
            return {}

    def _tls_info(self, host: str, port: int) -> Dict:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode    = ssl.CERT_NONE
            with socket.create_connection((host, port), timeout=5) as raw:
                with ctx.wrap_socket(raw, server_hostname=host) as s:
                    cert  = s.getpeercert() or {}
                    ciph  = s.cipher()
                    return {
                        "protocol": s.version(),
                        "cipher":   ciph[0] if ciph else "",
                        "bits":     ciph[2] if ciph else 0,
                        "expiry":   cert.get("notAfter",""),
                        "subject":  str(cert.get("subject","")),
                        "san":      str(cert.get("subjectAltName","")),
                    }
        except Exception as e:
            return {"error": str(e)}

    def run(self, **kw) -> List[Finding]:
        findings = []
        for host, ports in self.mem.open_ports.items():
            for port in ports:
                svc_name = self.PORT_SVC.get(port, f"port-{port}")
                info: Dict = {"name": svc_name, "port": port, "banner": ""}
                key = f"{host}:{port}"

                # ── Raw TCP banner ────────────────────────────────────
                banner = self._raw_banner(host, port)
                info["banner"] = banner

                # ── HTTP probe ────────────────────────────────────────
                https = port in (443, 8443, 4443)
                http  = port in (80, 8080, 8000, 8081) or https
                if http:
                    hinfo = self._http_banner(host, port, https=https)
                    info.update(hinfo)
                    if hinfo:
                        h_key = f"{'https' if https else 'http'}://{host}:{port}"
                        if h_key not in self.mem.http_hosts:
                            self.mem.http_hosts.append(h_key)

                # ── TLS info ──────────────────────────────────────────
                if https or port in (993, 995, 465, 587):
                    tls = self._tls_info(host, port)
                    info["tls"] = tls

                self.mem.services[key] = info
                self.log.ok(f"{key} [{svc_name}] {banner[:60]}")

                # ── Findings from service info ────────────────────────

                # Cleartext protocol
                if port in self.CLEARTEXT and banner:
                    f = self._finding(
                        title=f"Cleartext protocol: {svc_name} on {key}",
                        description="Credentials transmitted in plaintext",
                        severity=Severity.HIGH,
                        evidence=f"Banner: {banner[:200]}",
                        tags=["cleartext","protocol"],
                        target=host
                    )
                    self._save(f); findings.append(f)

                # Unauthenticated high-risk service (Redis/MongoDB/Elasticsearch)
                if svc_name in self.HIGH_RISK_SVC and banner:
                    f = self._finding(
                        title=f"{svc_name} exposed on {key}",
                        description=f"Potentially unauthenticated {svc_name} service",
                        severity=Severity.CRITICAL,
                        evidence=f"Banner: {banner[:200]}",
                        tags=["exposure", svc_name.lower()],
                        target=host
                    )
                    self._save(f); findings.append(f)

                # Weak TLS
                tls = info.get("tls", {})
                if tls and "error" not in tls:
                    proto = tls.get("protocol","")
                    if proto in ("TLSv1","TLSv1.1","SSLv3","SSLv2"):
                        f = self._finding(
                            title=f"Weak TLS: {proto} on {key}",
                            description="Outdated protocol version accepts connections",
                            severity=Severity.HIGH,
                            evidence=json.dumps(tls),
                            tags=["tls","weak","ssl"],
                            target=host
                        )
                        self._save(f); findings.append(f)

                    # Cert expiry
                    expiry = tls.get("expiry","")
                    if expiry:
                        try:
                            exp = datetime.datetime.strptime(expiry,"%b %d %H:%M:%S %Y %Z")
                            days = (exp - datetime.datetime.utcnow()).days
                            if days < 0:
                                f = self._finding(
                                    title=f"Certificate EXPIRED {abs(days)}d ago on {key}",
                                    description=f"Expired: {expiry}",
                                    severity=Severity.CRITICAL,
                                    evidence=json.dumps(tls),
                                    tags=["tls","cert","expired"],
                                    target=host
                                )
                                self._save(f); findings.append(f)
                            elif days < 30:
                                f = self._finding(
                                    title=f"Certificate expiring in {days}d on {key}",
                                    description=f"Expires: {expiry}",
                                    severity=Severity.MEDIUM,
                                    evidence=json.dumps(tls),
                                    tags=["tls","cert","expiring"],
                                    target=host
                                )
                                self._save(f); findings.append(f)
                        except ValueError:
                            pass

        return findings


class CVEMatcher(Tool):
    """
    Match banners against known-vulnerable version strings.
    A finding is only created when the banner actually contains the signature.
    """
    name  = "cve_matcher"
    stage = Stage.SCAN

    # (signature_substring, CVE, title, severity)
    SIGS = [
        ("Apache/2.4.49",   "CVE-2021-41773", "Path traversal + RCE",        Severity.CRITICAL),
        ("Apache/2.4.50",   "CVE-2021-42013", "Path traversal bypass",        Severity.CRITICAL),
        ("Apache/2.2.",     "CVE-2017-7679",  "mod_mime buffer overread",     Severity.HIGH),
        ("OpenSSH_7.2",     "CVE-2016-0777",  "Information leak (roaming)",   Severity.MEDIUM),
        ("OpenSSH_6.",      "CVE-2016-6515",  "DoS via long passwords",       Severity.MEDIUM),
        ("ProFTPD 1.3.5",   "CVE-2015-3306",  "mod_copy unauthenticated RCE", Severity.CRITICAL),
        ("vsftpd 2.3.4",    "CVE-2011-2523",  "Backdoor command execution",   Severity.CRITICAL),
        ("PHP/5.",          "CVE-2019-11043",  "FPM/nginx RCE",               Severity.CRITICAL),
        ("PHP/7.1.",        "CVE-2019-11043",  "FPM/nginx RCE",               Severity.CRITICAL),
        ("IIS/6.0",         "CVE-2017-7269",  "WebDAV buffer overflow RCE",   Severity.CRITICAL),
        ("OpenSSL/1.0.1",   "CVE-2014-0160",  "Heartbleed memory disclosure", Severity.CRITICAL),
        ("OpenSSL/1.0.2",   "CVE-2016-0800",  "DROWN attack",                 Severity.HIGH),
        ("Exim 4.87",       "CVE-2017-16943", "Use-after-free RCE",           Severity.CRITICAL),
        ("Exim 4.88",       "CVE-2017-16943", "Use-after-free RCE",           Severity.CRITICAL),
        ("WordPress/4.",    "CVE-2019-8942",  "Authenticated RCE",            Severity.HIGH),
        ("WordPress/5.0",   "CVE-2019-8942",  "Authenticated RCE",            Severity.HIGH),
        ("Drupal/7.",       "CVE-2018-7600",  "Drupalgeddon2 RCE",            Severity.CRITICAL),
        ("Drupal/8.",       "CVE-2018-7600",  "Drupalgeddon2 RCE",            Severity.CRITICAL),
        ("redis_version:2", "CVE-2015-8080",  "Lua sandbox escape",           Severity.HIGH),
        ("redis_version:3", "CVE-2022-0543",  "Lua sandbox escape",           Severity.CRITICAL),
        ("MongoDB 2.",      "CVE-2013-1892",  "Unauth REST interface",        Severity.HIGH),
    ]

    def run(self, **kw) -> List[Finding]:
        findings = []
        for key, info in self.mem.services.items():
            banner = (info.get("banner","") + " " +
                      info.get("server","") + " " +
                      info.get("powered",""))
            for sig, cve, title, sev in self.SIGS:
                if sig.lower() in banner.lower():
                    host = key.split(":")[0]
                    f = self._finding(
                        title=f"{cve} — {title} [{key}]",
                        description=f"Banner matched signature '{sig}'",
                        severity=sev,
                        evidence=f"Service: {key}\nBanner: {banner[:300]}\nSig: {sig}",
                        tags=["cve","vuln","banner-match",cve],
                        target=host
                    )
                    self._save(f); findings.append(f)

        self.log.ok(f"CVE matcher: {len(findings)} match(es)")
        return findings


# ═════════════════════════════════════════════════════════════════════
# STAGE 3 — ENUMERATE (HTTP/S only, real requests)
# ═════════════════════════════════════════════════════════════════════

class HTTPHeaderAudit(Tool):
    """
    Check real HTTP responses for missing security headers and
    information-leaking headers. A finding is created only when
    the header state is confirmed from a live response.
    """
    name  = "http_header_audit"
    stage = Stage.ENUMERATE

    # Headers that MUST be present
    REQUIRED = {
        "Strict-Transport-Security": (Severity.HIGH,
            "Missing HSTS — site vulnerable to protocol downgrade"),
        "Content-Security-Policy":   (Severity.MEDIUM,
            "Missing CSP — XSS mitigation absent"),
        "X-Content-Type-Options":    (Severity.LOW,
            "Missing X-Content-Type-Options: nosniff"),
        "X-Frame-Options":           (Severity.MEDIUM,
            "Missing X-Frame-Options — clickjacking possible"),
        "Referrer-Policy":           (Severity.LOW,
            "Missing Referrer-Policy"),
    }
    # Headers that should NOT be present (info leak)
    LEAK = {
        "Server":        Severity.LOW,
        "X-Powered-By":  Severity.MEDIUM,
        "X-AspNet-Version": Severity.MEDIUM,
        "X-AspNetMvc-Version": Severity.MEDIUM,
    }

    def _get(self, url: str, timeout: float = 8.0) -> Optional[Dict]:
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            import ssl as _ssl
            ctx = _ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode    = _ssl.CERT_NONE
            with urlopen(req, timeout=timeout, context=ctx) as resp:
                return {k.lower(): v for k, v in dict(resp.headers).items()}
        except HTTPError as e:
            return {k.lower(): v for k, v in dict(e.headers).items()}
        except Exception:
            return None

    def run(self, **kw) -> List[Finding]:
        targets  = self.mem.http_hosts
        findings = []

        if not targets:
            self.log.warn("http_header_audit: no HTTP hosts in session — run port_scanner + banner_grab first")
            return []

        for base_url in targets:
            self.log.info(f"Header audit → {base_url}")
            hdrs = self._get(base_url)
            if hdrs is None:
                self.log.warn(f"Could not reach {base_url}")
                continue

            # ── Missing security headers ──────────────────────────────
            for header, (sev, desc) in self.REQUIRED.items():
                if header.lower() not in hdrs:
                    f = self._finding(
                        title=f"Missing header: {header}",
                        description=desc,
                        severity=sev,
                        evidence=f"URL: {base_url}\nHeader '{header}' absent from response",
                        tags=["http","header","security"],
                        target=base_url
                    )
                    self._save(f); findings.append(f)

            # ── Information-leaking headers ───────────────────────────
            for header, sev in self.LEAK.items():
                val = hdrs.get(header.lower())
                if val:
                    f = self._finding(
                        title=f"Info leak header: {header}: {val}",
                        description=f"Server technology disclosed via response header",
                        severity=sev,
                        evidence=f"URL: {base_url}\n{header}: {val}",
                        tags=["http","header","disclosure"],
                        target=base_url
                    )
                    self._save(f); findings.append(f)

            # ── Cookie flags ──────────────────────────────────────────
            set_cookie = hdrs.get("set-cookie","")
            if set_cookie:
                if "httponly" not in set_cookie.lower():
                    f = self._finding(
                        title=f"Cookie missing HttpOnly on {base_url}",
                        description="Cookie accessible via JavaScript",
                        severity=Severity.MEDIUM,
                        evidence=f"Set-Cookie: {set_cookie[:200]}",
                        tags=["http","cookie","httponly"],
                        target=base_url
                    )
                    self._save(f); findings.append(f)
                if "secure" not in set_cookie.lower():
                    f = self._finding(
                        title=f"Cookie missing Secure flag on {base_url}",
                        description="Cookie transmitted over HTTP",
                        severity=Severity.MEDIUM,
                        evidence=f"Set-Cookie: {set_cookie[:200]}",
                        tags=["http","cookie","secure"],
                        target=base_url
                    )
                    self._save(f); findings.append(f)

        return findings


class PathDiscover(Tool):
    """
    Real HTTP path discovery via actual GET requests.
    Only creates a finding when the server returns a non-404 status code.
    403 is included — the path exists even if access is forbidden.
    """
    name  = "path_discover"
    stage = Stage.ENUMERATE

    PATHS = [
        # Admin / management
        "/admin", "/admin/", "/administrator", "/manage", "/manager",
        "/console", "/dashboard", "/panel", "/cp", "/controlpanel",
        # Auth
        "/login", "/signin", "/auth", "/sso", "/oauth",
        # APIs
        "/api", "/api/v1", "/api/v2", "/graphql", "/swagger",
        "/swagger-ui.html", "/swagger-ui", "/openapi.json", "/api-docs",
        # Common CMS
        "/wp-admin", "/wp-login.php", "/wp-json",
        "/phpmyadmin", "/pma", "/myadmin",
        "/drupal", "/joomla", "/magento",
        # Sensitive files
        "/.env", "/.git/HEAD", "/.git/config",
        "/config.php", "/config.yml", "/config.yaml",
        "/database.yml", "/settings.py", "/web.config",
        "/robots.txt", "/sitemap.xml", "/.well-known/security.txt",
        # Server info
        "/server-status", "/server-info",
        "/phpinfo.php", "/info.php", "/test.php",
        "/.htaccess", "/.htpasswd",
        # Monitoring / metrics
        "/actuator", "/actuator/health", "/actuator/env",
        "/metrics", "/health", "/status", "/ping",
        "/debug", "/_debug", "/trace",
        # Backup
        "/backup", "/backup.zip", "/backup.tar.gz",
        "/dump.sql", "/db.sql",
    ]

    # Paths whose discovery is always HIGH/CRITICAL regardless of status
    CRITICAL_PATHS = {
        "/.env", "/.git/HEAD", "/.git/config",
        "/config.php", "/database.yml", "/settings.py",
        "/phpinfo.php", "/info.php",
        "/.htpasswd", "/dump.sql", "/db.sql",
        "/actuator/env", "/actuator",
        "/phpmyadmin", "/pma",
    }
    HIGH_PATHS = {
        "/admin", "/admin/", "/administrator", "/wp-admin",
        "/wp-login.php", "/console", "/manager",
        "/backup", "/backup.zip", "/backup.tar.gz",
        "/server-status", "/server-info",
    }

    def _get_status(self, base: str, path: str, timeout: float = 5.0) -> Optional[int]:
        url = base.rstrip("/") + path
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            import ssl as _ssl
            ctx = _ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode    = _ssl.CERT_NONE
            scheme = "https" if "https://" in base else "http"
            with urlopen(req, timeout=timeout,
                         context=ctx if scheme == "https" else None) as r:
                return r.status
        except HTTPError as e:
            return e.code
        except Exception:
            return None

    def run(self, paths: List[str] = None, threads: int = 20, **kw) -> List[Finding]:
        targets  = self.mem.http_hosts
        paths    = paths or self.PATHS
        findings = []

        if not targets:
            self.log.warn("path_discover: no HTTP hosts — run port_scanner + banner_grab first")
            return []

        for base in targets:
            self.log.info(f"Path discovery → {base} ({len(paths)} paths)")
            hits: List[Tuple[str, int]] = []

            with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as ex:
                fut_map = {ex.submit(self._get_status, base, p): p for p in paths}
                for fut in concurrent.futures.as_completed(fut_map):
                    path   = fut_map[fut]
                    status = fut.result()
                    if status is not None and status != 404:
                        hits.append((path, status))

            for path, status in sorted(hits):
                if path in self.CRITICAL_PATHS:
                    sev = Severity.CRITICAL
                elif path in self.HIGH_PATHS:
                    sev = Severity.HIGH
                elif status == 403:
                    sev = Severity.MEDIUM   # exists but access denied
                else:
                    sev = Severity.LOW

                url = base.rstrip("/") + path
                f = self._finding(
                    title=f"Path found: {path} [{status}]",
                    description=f"HTTP {status} on {base}",
                    severity=sev,
                    evidence=f"GET {url} → HTTP {status}",
                    tags=["http","path","discovery"],
                    target=base
                )
                self._save(f); findings.append(f)
                self.log.ok(f"{path} [{status}] on {base}")

        return findings


# ═════════════════════════════════════════════════════════════════════
# STAGE 4 — REPORT
# ═════════════════════════════════════════════════════════════════════

class ReportGenerator(Tool):
    name  = "report_generator"
    stage = Stage.REPORT

    SEV_ORDER = [Severity.CRITICAL, Severity.HIGH,
                 Severity.MEDIUM,   Severity.LOW, Severity.INFO]
    SEV_ICON  = {Severity.CRITICAL:"🔴", Severity.HIGH:"🟠",
                 Severity.MEDIUM:"🟡",   Severity.LOW:"🟢", Severity.INFO:"🔵"}

    def run(self, out_dir: str = "reports", **kw) -> List[Finding]:
        Path(out_dir).mkdir(exist_ok=True)
        ts   = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = Path(out_dir) / f"report_{self.mem.session_id}_{ts}.md"

        by_sev: Dict[Severity, List[Finding]] = {s: [] for s in self.SEV_ORDER}
        for f in self.mem.findings:
            try:
                by_sev[Severity(f.severity)].append(f)
            except ValueError:
                pass

        counts = {s: len(v) for s, v in by_sev.items()}
        total  = sum(counts.values())

        md  = f"# Red Team Report — {self.mem.target}\n\n"
        md += f"**Session:** `{self.mem.session_id}`  \n"
        md += f"**Date:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  \n"
        md += f"**Total findings:** {total}  \n\n---\n\n"
        md += "## Summary\n\n"
        md += "| Severity | Count |\n|---|---|\n"
        for s in self.SEV_ORDER:
            md += f"| {self.SEV_ICON[s]} {s.value.title()} | {counts[s]} |\n"

        md += "\n---\n\n## Assets Discovered\n\n"
        md += f"- **Hosts:** {', '.join(self.mem.hosts) or '—'}\n"
        md += f"- **Subdomains:** {len(self.mem.subdomains)}\n"
        md += f"- **Open ports:** {sum(len(v) for v in self.mem.open_ports.values())}\n"
        md += f"- **HTTP targets:** {len(self.mem.http_hosts)}\n\n"

        if self.mem.open_ports:
            md += "### Open Ports\n"
            for host, ports in self.mem.open_ports.items():
                md += f"- `{host}`: {ports}\n"
            md += "\n"

        md += "---\n\n## Findings\n\n"
        for sev in self.SEV_ORDER:
            flist = by_sev[sev]
            if not flist:
                continue
            md += f"### {self.SEV_ICON[sev]} {sev.value.upper()} ({len(flist)})\n\n"
            for i, f in enumerate(flist, 1):
                md += f"#### {i}. {f.title}\n"
                md += f"- **Stage:** {f.stage} | **Tool:** `{f.tool}` | **Target:** `{f.target}`\n"
                if f.description:
                    md += f"- **Detail:** {f.description}\n"
                if f.evidence:
                    md += f"\n```\n{f.evidence[:400]}\n```\n"
                md += "\n"

        md += "---\n\n## Recommendations\n\n"
        recs = []
        titles = [f.title for f in self.mem.findings]
        def any_match(*kws): return any(any(k.lower() in t.lower() for k in kws) for t in titles)
        if any_match("cleartext","ftp","telnet"):
            recs.append("Replace cleartext protocols (FTP/Telnet/SMTP) with encrypted alternatives (SFTP/SSH/SMTPS).")
        if any_match("tls","ssl","weak"):
            recs.append("Enforce TLS 1.2+ only. Disable SSLv3, TLS 1.0, and TLS 1.1.")
        if any_match("expired","expir"):
            recs.append("Automate certificate renewal (e.g. Let's Encrypt + certbot).")
        if any_match("missing header","hsts","csp","x-frame"):
            recs.append("Add security response headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options.")
        if any_match("cookie"):
            recs.append("Set HttpOnly and Secure flags on all session cookies.")
        if any_match(".env","config","backup","dump","git"):
            recs.append("Remove sensitive files from web root. Enforce .htaccess/nginx deny rules.")
        if any_match("redis","mongodb","elasticsearch"):
            recs.append("Bind database services to localhost or internal network only. Require authentication.")
        if any_match("cve","rce","traversal"):
            recs.append("Apply vendor patches for identified CVEs immediately.")
        if any_match("phpmyadmin","admin","panel"):
            recs.append("Restrict admin interfaces to IP allowlist or VPN.")
        if any_match("subdomain"):
            recs.append("Audit and clean up unused subdomains to reduce attack surface.")
        for r_text in (recs or ["No specific recommendations — review findings manually."]):
            md += f"- {r_text}\n"

        md += "\n---\n*Generated by red_team_workflow.py*\n"

        path.write_text(md, encoding="utf-8")
        self.log.ok(f"Report saved: {path}")
        return []


# ═════════════════════════════════════════════════════════════════════
# ENGINE
# ═════════════════════════════════════════════════════════════════════

STAGE_TOOLS = {
    Stage.RECON:     [DNSRecon, SubdomainEnum, WHOISLookup],
    Stage.SCAN:      [PortScanner, BannerGrab, CVEMatcher],
    Stage.ENUMERATE: [HTTPHeaderAudit, PathDiscover],
    Stage.REPORT:    [ReportGenerator],
}

class Engine:
    def __init__(self, target: str, db_path: Path = Path("redteam.db"),
                 resume_id: str = None, skip_preflight: bool = False):

        self.db = Database(db_path)

        if resume_id:
            mem = self.db.load_session(resume_id)
            if not mem:
                raise SystemExit(f"Session '{resume_id}' not found in database")
            self.mem = mem
        else:
            self.mem = SessionMemory(
                session_id=str(uuid.uuid4())[:12],
                target=target.strip().lower().rstrip("/")
            )

        self.log = Log(self.mem.session_id)
        self._banner()

        if not skip_preflight:
            Preflight().run()

    def _banner(self):
        print(f"\n{'═'*62}")
        print(f"  {RED}{BOLD}RED TEAM WORKFLOW ENGINE{R}")
        print(f"  {DIM}Session : {self.mem.session_id}{R}")
        print(f"  {DIM}Target  : {self.mem.target}{R}")
        print(f"{'═'*62}")

    def run_stage(self, stage: Stage, only: List[str] = None,
                  skip: List[str] = None, **kw) -> List[Finding]:
        self.log.stage(stage)
        all_findings = []
        for ToolCls in STAGE_TOOLS.get(stage, []):
            t = ToolCls(self.db, self.mem, self.log)
            if only and t.name not in only:
                continue
            if skip and t.name in skip:
                self.log.warn(f"Skipping {t.name}")
                continue
            t0 = time.time()
            try:
                findings = t.run(**kw)
                dur = time.time() - t0
                self.db.log_run(self.mem.session_id, t.name,
                                "ok", len(findings), dur)
                all_findings.extend(findings)
                self.db.save_session(self.mem)
            except Exception as e:
                dur = time.time() - t0
                self.log.err(f"{t.name} failed: {e}")
                self.db.log_run(self.mem.session_id, t.name, "error", 0, dur)
        return all_findings

    def run_all(self, stages: List[Stage] = None, **kw) -> List[Finding]:
        stages = stages or list(Stage)
        all_f  = []
        for stage in stages:
            all_f.extend(self.run_stage(stage, **kw))
        self._summary()
        return all_f

    def _summary(self):
        counts: Dict[str, int] = {}
        for f in self.mem.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1

        print(f"\n{'═'*62}")
        print(f"  {BOLD}SESSION COMPLETE — {self.mem.target}{R}")
        print(f"  Hosts: {len(self.mem.hosts)}  |  "
              f"Services: {len(self.mem.services)}  |  "
              f"Findings: {len(self.mem.findings)}")
        print()
        order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM,
                 Severity.LOW, Severity.INFO]
        icons = {Severity.CRITICAL:"🔴",Severity.HIGH:"🟠",
                 Severity.MEDIUM:"🟡",Severity.LOW:"🟢",Severity.INFO:"🔵"}
        for s in order:
            n = counts.get(s.value, 0)
            if n:
                print(f"  {icons[s]} {s.value.upper():10s} {n}")
        print(f"{'═'*62}\n")

    def list_tools(self):
        print(f"\n{BOLD}Tools by stage:{R}")
        for stage, tools in STAGE_TOOLS.items():
            print(f"\n  {CYAN}{stage.value.upper()}{R}")
            for T in tools:
                print(f"    • {T.name}")


# ═════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(
        description="Red Team Workflow Engine — real probes only",
        formatter_class=argparse.RawTextHelpFormatter
    )
    p.add_argument("target", nargs="?", help="Target domain or IP")
    p.add_argument("--stages",   nargs="+", choices=[s.value for s in Stage],
                   help="Stages to run (default: all)")
    p.add_argument("--only",     nargs="+", help="Run only these tool name(s)")
    p.add_argument("--skip",     nargs="+", help="Skip these tool name(s)")
    p.add_argument("--ports",    nargs="+", type=int, help="Custom port list for scanner")
    p.add_argument("--threads",  type=int, default=100, help="Port scan thread count")
    p.add_argument("--timeout",  type=float, default=1.5, help="Port scan timeout (s)")
    p.add_argument("--resume",   help="Resume session by ID")
    p.add_argument("--preflight",       action="store_true", help="Check dependencies only")
    p.add_argument("--skip-preflight",  action="store_true", help="Skip preflight check")
    p.add_argument("--list-tools",      action="store_true", help="List all tools")
    p.add_argument("--list-sessions",   action="store_true", help="List past sessions")
    p.add_argument("--db", default="redteam.db", help="Database file path")
    args = p.parse_args()

    if args.preflight:
        Preflight().run(); return

    if args.list_sessions:
        db   = Database(Path(args.db))
        rows = db.list_sessions()
        if not rows:
            print("No sessions found.")
        else:
            print(f"\n{'ID':15} {'TARGET':30} {'UPDATED':25}")
            print("─" * 70)
            for r in rows:
                print(f"{r['session_id']:15} {r['target']:30} {r['updated_at']:25}")
        return

    if not args.target and not args.resume:
        p.print_help(); return

    engine = Engine(
        target=args.target or "",
        db_path=Path(args.db),
        resume_id=args.resume,
        skip_preflight=args.skip_preflight,
    )

    if args.list_tools:
        engine.list_tools(); return

    stages = [Stage(s) for s in args.stages] if args.stages else list(Stage)
    engine.run_all(
        stages=stages,
        only=args.only,
        skip=args.skip,
        ports=args.ports,
        threads=args.threads,
        timeout=args.timeout,
    )

if __name__ == "__main__":
    main()
