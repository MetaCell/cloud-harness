#!/usr/bin/env bash
# Thin wrapper — implementation moved to nfsvol create.
# Kept for backward compatibility with any external callers.
#
# Original flags: -m <mountpoint> -s <size_bytes> [--mountonly]
# nfsvol create does not support --mountonly (mount-all handles that path).

set -e

mountpoint=""
size=""
mountonly=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        -m) mountpoint="$2"; shift 2 ;;
        -s) size="$2"; shift 2 ;;
        --mountonly) mountonly=1; shift ;;
        --) shift; break ;;
        *) shift ;;
    esac
done

if [[ $mountonly -eq 1 ]]; then
    # mount-only path: let mount-all handle this, but support single-path invocation
    # by running nfsvol mount-all and letting it skip already-mounted volumes.
    exec /usr/local/bin/nfsvol mount-all
fi

exec /usr/local/bin/nfsvol create -m "${mountpoint}" -s "${size}"
