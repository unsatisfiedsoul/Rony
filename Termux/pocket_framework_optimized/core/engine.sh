#!/data/data/com.termux/files/usr/bin/bash
run_module() {
    module=$1
    target=$2
    if [[ -f "../modules/$module.sh" ]]; then
        source "../modules/$module.sh"
        execute "$target"
    else
        echo "[!] Module not found"
    fi
}
