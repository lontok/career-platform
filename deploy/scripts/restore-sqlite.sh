#!/usr/bin/env bash
set -euo pipefail
umask 077

if [[ "$#" -ne 2 ]]; then
    echo "Usage: $0 <backup-file> <target-database>" >&2
    exit 64
fi

backup_file="$1"
target_database="$2"
target_directory="$(dirname -- "$target_database")"

if [[ ! -f "$backup_file" ]]; then
    echo "Backup file does not exist or is not a regular file: $backup_file" >&2
    exit 66
fi

if [[ ! -d "$target_directory" ]]; then
    echo "Target directory does not exist: $target_directory" >&2
    exit 73
fi

if [[ -e "$target_database" ||
    -e "${target_database}-journal" ||
    -e "${target_database}-shm" ||
    -e "${target_database}-wal" ]]; then
    echo "Refusing to overwrite an existing database or SQLite sidecar." >&2
    exit 73
fi

trap 'rm -f -- "$target_database"' ERR
install -m 600 "$backup_file" "$target_database"

integrity_check="$(sqlite3 "$target_database" "PRAGMA integrity_check;")"
if [[ "$integrity_check" != "ok" ]]; then
    echo "Restored database integrity check failed: $integrity_check" >&2
    exit 65
fi

trap - ERR
echo "$target_database"
