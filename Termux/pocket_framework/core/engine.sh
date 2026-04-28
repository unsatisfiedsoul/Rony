#!/data/data/com.termux/files/usr/bin/bash

run_module() {
    local module_name="$1"
    local target="$2"
    
    # 1. Initialize the specific folder for this target
    set_target_dir "$target"
    
    local module_path="$MODULES_DIR/${module_name}.sh"

    if [[ -f "$module_path" ]]; then
        log_info "Executing $module_name on $target..."
        source "$module_path"
        execute "$target"
        unset -f execute
    else
        log_error "Module '$module_name' not found at: $module_path"
    fi
}
