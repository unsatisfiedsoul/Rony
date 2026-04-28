#!/data/data/com.termux/files/usr/bin/bash

# This script provides parallel task management.
# It relies on MAX_JOBS being defined in config.sh.

run_job() {
    # 1. Fallback for MAX_JOBS if not defined
    local max=${MAX_JOBS:-2}
    
    # 2. Throttling Logic
    # Count only running background jobs in the current shell context
    local running_jobs
    running_jobs=$(jobs -r | wc -l)

    if (( running_jobs >= max )); then
        log_debug "Job limit reached ($max). Waiting for a slot..."
        
        while (( $(jobs -r | wc -l) >= max )); do
            sleep 1
        done
    fi

    # 3. Execution
    # "$@" passes all arguments exactly as received (e.g., "bash module.sh target")
    log_debug "Starting job: $1 $2"
    "$@" &
    
    # Optional: Brief sleep to prevent a "thundering herd" if 
    # starting many fast processes at once.
    sleep 0.2
}

# Helper to wait for all background tasks before proceeding
wait_all() {
    log_info "Waiting for background tasks to complete..."
    wait
    log_info "All background tasks finished."
}
