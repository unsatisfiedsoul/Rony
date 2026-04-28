#!/data/data/com.termux/files/usr/bin/bash
execute() {
    target=$1

    source ../core/jobs.sh
    source ../modules/recon.sh
    execute "$target"

    source ../modules/scan.sh
    execute "$target"

    source ../core/decision.sh
    services=$(detect_services "$OUTPUT_DIR/scan_$target.txt")

    for svc in $services; do
        case $svc in
            web)
                run_job bash ../modules/web.sh "$target"
                ;;
            smb)
                run_job bash ../modules/enum.sh "$target"
                ;;
        esac
    done

    wait

    source ../modules/loot.sh
    execute "$target"

    log SUCCESS "Done"
}
