#!/data/data/com.termux/files/usr/bin/bash

cd "$(dirname "$0")"

termux-wake-lock

source core/config.sh
source core/logger.sh
source core/engine.sh

while true; do
    echo "1) Intelligent Fast Pipeline"
    echo "0) Exit"
    read -p "Select: " opt
    read -p "Target: " target

    case $opt in
        1) run_module intel_pipeline "$target" ;;
        0) exit ;;
    esac
done
