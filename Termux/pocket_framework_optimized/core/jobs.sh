#!/data/data/com.termux/files/usr/bin/bash
run_job() {
    while (( $(jobs -r | wc -l) >= MAX_JOBS )); do
        sleep 1
    done
    "$@" &
}
