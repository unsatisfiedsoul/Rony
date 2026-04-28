#!/data/data/com.termux/files/usr/bin/bash

# --- 1. Environment Setup ---
# Force the script to recognize its own directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# --- 2. Load Core Dependencies ---
# We check if files exist before sourcing to prevent crash loops
if [[ -f "core/config.sh" ]]; then
    source core/config.sh
    source core/logger.sh
    source core/engine.sh
else
    echo "[!] Critical Error: core/config.sh not found in $SCRIPT_DIR"
    exit 1
fi

# --- 3. Cleanup & Protection ---
# Ensure termux-wake-lock is active and will be released on exit
termux-wake-lock
cleanup() {
    echo -e "\n\n[*] Shutting down..."
    termux-wake-unlock
    exit 0
}
trap cleanup SIGINT SIGTERM

# --- 4. Main User Interface ---
clear
echo "================================================="
echo "        POCKET FRAMEWORK: INTEL ENGINE"
echo "        Root: $PROJECT_ROOT"
echo "================================================="

while true; do
    echo -e "\n[ Main Menu ]"
    echo "1) Intelligent Fast Pipeline"
    echo "0) Exit"
    echo "-------------------------------------------------"
    
    read -p "Select option: " opt

    case "$opt" in
        1)
            echo -e "\n[ Configuration ]"
            read -p "Enter Target (IP or Domain): " target
            
            if [[ -z "$target" ]]; then
                log_error "Target cannot be empty. Please try again."
                continue
            fi

            log_info "Launching Intelligent Pipeline for $target..."
            # run_module is defined in core/engine.sh
            run_module intel_pipeline "$target"
            ;;
            
        0)
            cleanup
            ;;
            
        *)
            echo -e "\n[!] Invalid option: '$opt'"
            ;;
    esac
done
