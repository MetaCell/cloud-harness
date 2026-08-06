#!/usr/bin/env bash
# Thin wrapper — implementation moved to nfsvol delete.
# Kept for backward compatibility with any external callers.

set -e

mountpoint=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -m) mountpoint="$2"; shift 2 ;;
        --) shift; break ;;
        *) shift ;;
    esac
done

exec /usr/local/bin/nfsvol delete -m "${mountpoint}"
