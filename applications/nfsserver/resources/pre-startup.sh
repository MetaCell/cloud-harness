#!/bin/bash
# Thin wrapper — kept for backward compatibility. Bootstrap is now handled
# by run_nfs.sh calling nfsvol mount-all directly.
exec /usr/local/bin/nfsvol mount-all
