#!/usr/bin/env bash
set -euo pipefail
umask 077

if [[ "$#" -ne 2 ]]; then
    echo "Usage: $0 <source-database> <backup-directory>" >&2
    exit 64
fi

source_database="$1"
backup_directory="$2"

if [[ ! -f "$source_database" ]]; then
    echo "Source database does not exist or is not a regular file: $source_database" >&2
    exit 66
fi

mkdir -p "$backup_directory"
chmod 700 "$backup_directory"

backup_file="$backup_directory/resume-$(date -u +%Y%m%dT%H%M%SZ)-$$.db"
case "$backup_file" in
    *"'"* | *$'\n'*)
        echo "Backup path must not contain quotes or newlines." >&2
        exit 64
        ;;
esac

sqlite3 "$source_database" ".backup '$backup_file'"
chmod 600 "$backup_file"

integrity_check="$(sqlite3 "$backup_file" "PRAGMA integrity_check;")"
if [[ "$integrity_check" != "ok" ]]; then
    rm -f -- "$backup_file"
    echo "Backup integrity check failed: $integrity_check" >&2
    exit 65
fi

echo "$backup_file"
