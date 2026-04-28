#!/data/data/com.termux/files/usr/bin/bash

# Define colors for Termux terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure LOG_FILE has a default if not set in config.sh
LOG_FILE="${LOG_FILE:-/data/data/com.termux/files/home/session.log}"

# Core logging function
log_message() {
    local level="$1"
    local message="$2"
    local color="$3"
    local timestamp
    timestamp=$(date '+%H:%M:%S')

    # Format for the file (no colors)
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"

    # Format for the terminal (with colors)
    echo -e "${color}[$timestamp] [$level]${NC} $message"
}

# Helper functions for cleaner code in other scripts
log_info() {
    log_message "INFO" "$1" "$GREEN"
}

log_warn() {
    log_message "WARN" "$1" "$YELLOW"
}

log_error() {
    log_message "ERROR" "$1" "$RED"
}

log_debug() {
    log_message "DEBUG" "$1" "$BLUE"
}
