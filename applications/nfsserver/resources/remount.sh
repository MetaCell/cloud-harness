#!/bin/bash
# Thin wrapper — implementation moved to nfsvol mount-all.
# Kept for backward compatibility with any external callers.
exec /usr/local/bin/nfsvol mount-all
