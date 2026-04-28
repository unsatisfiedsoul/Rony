#!/data/data/com.termux/files/usr/bin/bash

execute() {
    local target="$1"
    
    log_info "Starting Intelligent Pipeline for: $target"

    # 1. RECON (Always first)
    run_module "recon" "$target" || { log_error "Recon failed"; return 1; }

    # 2. SCAN (Identify ports)
    run_module "scan" "$target"

    # 3. DECISION (Decide based on ports)
    # If your Decision.sh starts background jobs, make sure to use 'wait'
    log_debug "Entering Decision phase..."
    run_module "decision" "$target"
    
    # --- CRITICAL FIX ---
    # If Decision.sh launched anything in the background, wait for it to die
    wait 
    # --------------------

    # 4. FINAL LOOT (Only after everything else is 100% DONE)
    log_info "Finalizing results..."
    run_module "loot" "$target"

    log_info "Pipeline successfully finished for $target"
}
