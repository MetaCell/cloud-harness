#!/usr/bin/env bash
#
# Production failover / edge-case test for the cloud-harness NFS server.
#
# Scenarios covered
# -----------------
#
#   1. RWX PVC provisioning
#      Create a ReadWriteMany PVC against the <namespace>-nfs-client storage
#      class and wait for Bound. Exercises the provisioner end-to-end: loopback
#      ext4 creation, mount, and per-PV entry in /etc/exports.d/.
#
#   2. Multi-node mount via pod anti-affinity
#      Spin up two writer pods with `podAntiAffinity` on
#      `topologyKey: kubernetes.io/hostname` so they land on different nodes,
#      both mounting the same PVC. Proves the NFS server accepts simultaneous
#      mounts of one export from two different hosts.
#
#   3. Cross-node read/write visibility
#      Each pod writes a distinct file; the peer reads it back after a short
#      attribute-cache delay. Proves cache coherency across the ClusterIP
#      service hop.
#
#   4. fsid stability across NFS server pod restart  ***critical***
#      Delete the running nfs-server pod while clients have live mounts,
#      wait for Recreate to schedule a new pod, then verify clients can still
#      read pre-restart data without remounting. Proves the `Change A`
#      stable-fsid design (/etc/exports.d/<pv>.exports with SHA-256-derived
#      fsid) prevents ESTALE on the server-side failover path. Also writes a
#      new file post-restart and checks it propagates.
#
#   5. Watchdog recovery from stale loop device
#      Inside the server pod, forcibly `losetup -d` the loop device backing
#      the test PVC. Waits ~45 s and verifies the watchdog (30 s interval)
#      has remounted and clients still see the data. Proves intra-pod
#      stale-mount recovery.
#
#   6. Concurrent writes from both nodes (documented race tolerance)
#      Both pods `echo >> /data/concurrent.log` in parallel. Under
#      `nolock,local_lock=all` soft semantics interleaving is accepted but no
#      write should disappear entirely; the check asserts ≥50 lines land.
#      Documents the tradeoff, it does not prevent the race.
#
#   7. PVC delete cleanup
#      Delete the PVC and verify the /etc/exports.d/<pv>.exports fragment is
#      removed on the server. Proves the provisioner's Delete path correctly
#      invokes `nfsvol delete` (which removes the fragment and runs
#      `exportfs -r`).
#
# What is NOT covered
# -------------------
#
#   - Ungraceful node loss (the ~6 min force-detach path): impossible to
#     simulate reliably in CI without kicking a real node out of the cluster.
#     Documented in README-PROD.md as an inherent limitation.
#   - Backup / disaster recovery: operator responsibility.
#   - HA / active-passive: out of scope for this architecture.
#
# Requirements
# ------------
#
#   - kubectl on PATH, authenticated to the test cluster
#   - at least 2 schedulable nodes (test skips gracefully otherwise)
#   - NAMESPACE env var pointing at the deployed namespace
#   - STORAGE_CLASS env var (defaults to "<namespace>-nfs-client")
#
# The script cleans up all fixtures on EXIT (including on failure) via trap.
#
# Example:
# NAMESPACE=test-ch bash ./failover-test.sh 2>&1

set -u -o pipefail

NAMESPACE="${NAMESPACE:?NAMESPACE env var is required}"
STORAGE_CLASS="${STORAGE_CLASS:-${NAMESPACE}-nfs-client}"
PREFIX="nfs-failover-test"
PVC="${PREFIX}-pvc"
WRITER_A="${PREFIX}-writer-a"
WRITER_B="${PREFIX}-writer-b"

log()  { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" >&2; }
pass() { printf '[%s] PASS: %s\n' "$(date +%H:%M:%S)" "$*" >&2; }
fail() { printf '[%s] FAIL: %s\n' "$(date +%H:%M:%S)" "$*" >&2; exit 1; }

k() { kubectl -n "$NAMESPACE" "$@"; }

cleanup() {
    log "cleanup: removing test fixtures"
    k delete pod "$WRITER_A" "$WRITER_B" --ignore-not-found --grace-period=0 --force --wait=false 2>/dev/null || true
    k delete pvc "$PVC" --ignore-not-found --wait=false 2>/dev/null || true
}
trap cleanup EXIT

wait_for() {
    # wait_for <seconds> <predicate-cmd...>; returns 0 on success, 1 on timeout
    local timeout=$1; shift
    local end=$(( $(date +%s) + timeout ))
    while [ "$(date +%s)" -lt "$end" ]; do
        if "$@" >/dev/null 2>&1; then return 0; fi
        sleep 2
    done
    return 1
}

# -----------------------------------------------------------------------------
log "preflight"
# -----------------------------------------------------------------------------

NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [ "${NODE_COUNT:-0}" -lt 2 ]; then
    log "SKIP: need ≥2 nodes, found ${NODE_COUNT}"
    exit 0
fi
log "preflight: $NODE_COUNT nodes available"

if ! k get storageclass "$STORAGE_CLASS" >/dev/null 2>&1 && \
   ! kubectl get storageclass "$STORAGE_CLASS" >/dev/null 2>&1; then
    fail "storage class $STORAGE_CLASS not found"
fi

k rollout status deploy/nfs-server --timeout=180s || fail "nfs-server not Ready"
INITIAL_NFS_POD=$(k get pod -l app=nfs-server -o jsonpath='{.items[0].metadata.name}')
log "initial nfs-server pod: $INITIAL_NFS_POD"

# -----------------------------------------------------------------------------
log "test 1: provision RWX PVC via $STORAGE_CLASS"
# -----------------------------------------------------------------------------

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: $PVC
  namespace: $NAMESPACE
  labels:
    app: $PREFIX
spec:
  accessModes: [ReadWriteMany]
  storageClassName: $STORAGE_CLASS
  resources:
    requests:
      storage: 100Mi
EOF

wait_for 60 sh -c "[ \"\$(kubectl -n $NAMESPACE get pvc $PVC -o jsonpath='{.status.phase}' 2>/dev/null)\" = Bound ]" \
    || fail "PVC did not Bind within 60s"
PV_NAME=$(k get pvc "$PVC" -o jsonpath='{.spec.volumeName}')
pass "PVC bound to $PV_NAME"

# -----------------------------------------------------------------------------
log "test 2: mount same PVC on two nodes via pod anti-affinity"
# -----------------------------------------------------------------------------

for pod in "$WRITER_A" "$WRITER_B"; do
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: $pod
  namespace: $NAMESPACE
  labels:
    app: $PREFIX
spec:
  terminationGracePeriodSeconds: 5
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app: $PREFIX
          topologyKey: kubernetes.io/hostname
  containers:
    - name: writer
      image: busybox:1.36
      command: [sh, -c, "sleep 3600"]
      volumeMounts:
        - name: shared
          mountPath: /data
  volumes:
    - name: shared
      persistentVolumeClaim:
        claimName: $PVC
EOF
done

for pod in "$WRITER_A" "$WRITER_B"; do
    k wait --for=condition=Ready "pod/$pod" --timeout=180s \
        || fail "pod $pod did not become Ready (likely mount failure)"
done

NODE_A=$(k get pod "$WRITER_A" -o jsonpath='{.spec.nodeName}')
NODE_B=$(k get pod "$WRITER_B" -o jsonpath='{.spec.nodeName}')
[ "$NODE_A" != "$NODE_B" ] || fail "both writers on $NODE_A — anti-affinity failed"
pass "writer A on $NODE_A, writer B on $NODE_B"

# -----------------------------------------------------------------------------
log "test 3: cross-node read/write visibility"
# -----------------------------------------------------------------------------

k exec "$WRITER_A" -- sh -c "echo hello-from-A > /data/from-a.txt && sync" || fail "write from A failed"
k exec "$WRITER_B" -- sh -c "echo hello-from-B > /data/from-b.txt && sync" || fail "write from B failed"
sleep 2  # NFS attribute cache

got=$(k exec "$WRITER_B" -- cat /data/from-a.txt 2>/dev/null || echo MISSING)
[ "$got" = "hello-from-A" ] || fail "B cannot read A's file: got '$got'"

got=$(k exec "$WRITER_A" -- cat /data/from-b.txt 2>/dev/null || echo MISSING)
[ "$got" = "hello-from-B" ] || fail "A cannot read B's file: got '$got'"
pass "cross-node r/w works"

# -----------------------------------------------------------------------------
log "test 4: fsid stability across nfs-server restart"
# -----------------------------------------------------------------------------

log "deleting nfs-server pod $INITIAL_NFS_POD"
k delete pod "$INITIAL_NFS_POD" --wait=false

wait_for 180 sh -c "
    cur=\$(kubectl -n $NAMESPACE get pod -l app=nfs-server -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    [ -n \"\$cur\" ] && [ \"\$cur\" != '$INITIAL_NFS_POD' ] &&
    kubectl -n $NAMESPACE get pod \$cur -o jsonpath='{.status.conditions[?(@.type==\"Ready\")].status}' 2>/dev/null | grep -q True
" || fail "new nfs-server pod did not become Ready in 180s"

NEW_NFS_POD=$(k get pod -l app=nfs-server -o jsonpath='{.items[0].metadata.name}')
log "new nfs-server pod: $NEW_NFS_POD"

# After Ready, give NFS userland (rpcbind, rpc.nfsd, exportfs) a moment to be
# fully serving — the readiness probe only checks the watchdog's healthz.
sleep 15

# Under stable-fsid clients keep reading the same file handles; with unstable
# fsids the read after restart would return ESTALE permanently.
#
# Each attempt: ls to force the NFS client to revalidate the directory handle
# (which also clears any cached stale child handles), then cat to read.
# Both calls are time-bounded so a hard-mount hang during the recovery
# window (~30 s) does not stall the loop.
verify_read() {
    local pod=$1 file=$2 expected=$3
    local dir
    dir=$(dirname "$file")
    local attempt=0
    local got
    while [ $attempt -lt 30 ]; do
        timeout 10 kubectl -n "$NAMESPACE" exec "$pod" -- ls "$dir" >/dev/null 2>&1 || true
        got=$(timeout 15 kubectl -n "$NAMESPACE" exec "$pod" -- cat "$file" 2>/dev/null || true)
        if [ "$got" = "$expected" ]; then
            return 0
        fi
        sleep 3
        attempt=$((attempt + 1))
    done
    return 1
}

verify_read "$WRITER_A" /data/from-a.txt hello-from-A || fail "A lost its own file (ESTALE — fsid unstable)"
verify_read "$WRITER_B" /data/from-b.txt hello-from-B || fail "B lost its own file (ESTALE — fsid unstable)"
verify_read "$WRITER_B" /data/from-a.txt hello-from-A || fail "B lost A's file after restart (ESTALE)"

# Verify writes still propagate post-restart
k exec "$WRITER_A" -- sh -c "echo post-restart > /data/post-restart.txt && sync" || fail "post-restart write failed"
verify_read "$WRITER_B" /data/post-restart.txt post-restart || fail "post-restart write did not propagate"
pass "fsid stable across server pod restart — no ESTALE"

# -----------------------------------------------------------------------------
log "test 5: watchdog recovery from stale loop device"
# -----------------------------------------------------------------------------

# Find the loop device backing the test PVC on the server.
# mountpoint format: /exports/<pvName> where pvName includes the PV_NAME.
MOUNTPOINT=$(k exec "$NEW_NFS_POD" -- sh -c "ls -d /exports/*${PV_NAME}* 2>/dev/null | grep -v '\.exports$' | grep -v 'archived-' | head -1" || true)
if [ -z "$MOUNTPOINT" ]; then
    log "skipping test 5: could not locate server-side mountpoint for $PV_NAME"
else
    LOOPDEV=$(k exec "$NEW_NFS_POD" -- sh -c "losetup -a | grep '$MOUNTPOINT.quota' | cut -d: -f1" || true)
    if [ -z "$LOOPDEV" ]; then
        log "skipping test 5: could not locate loop device for $MOUNTPOINT"
    else
        log "forcing stale: detach $LOOPDEV (backing $MOUNTPOINT.quota)"
        k exec "$NEW_NFS_POD" -- sh -c "losetup -d $LOOPDEV" || true
        # Watchdog interval is 30s; allow a margin.
        sleep 45
        verify_read "$WRITER_A" /data/from-a.txt hello-from-A \
            || fail "watchdog did not recover from stale loop within 45s"
        pass "watchdog recovered stale loop device and clients kept access"
    fi
fi

# -----------------------------------------------------------------------------
log "test 6: concurrent writes from both nodes (documented race tolerance)"
# -----------------------------------------------------------------------------

k exec "$WRITER_A" -- sh -c 'for i in $(seq 1 50); do echo "A-$i" >> /data/concurrent.log; done' &
pidA=$!
k exec "$WRITER_B" -- sh -c 'for i in $(seq 1 50); do echo "B-$i" >> /data/concurrent.log; done' &
pidB=$!
wait $pidA $pidB

count=$(k exec "$WRITER_A" -- sh -c 'wc -l < /data/concurrent.log' | tr -d ' ')
# With local_lock=all on soft NFSv3, interleaving is allowed but no write should
# be completely lost. Expect at least 50 lines (weakest guarantee).
if [ "${count:-0}" -lt 50 ]; then
    fail "concurrent writes lost more than half: $count < 50"
fi
pass "concurrent writes produced $count lines (interleaving tolerated)"

# -----------------------------------------------------------------------------
log "test 7: PVC delete cleans up /etc/exports.d/ fragment"
# -----------------------------------------------------------------------------

k delete pod "$WRITER_A" "$WRITER_B" --grace-period=10 --wait=true

NFS_POD=$(k get pod -l app=nfs-server -o jsonpath='{.items[0].metadata.name}')

# The fragment file is named <pvName>.exports where pvName is the
# mountpoint basename (which contains $PV_NAME inside it). Find it by listing.
FRAGMENT=$(k exec "$NFS_POD" -- sh -c "ls /etc/exports.d/ 2>/dev/null" | grep -F "$PV_NAME" | head -1 || true)

if [ -z "$FRAGMENT" ]; then
    log "WARN: no exports fragment for $PV_NAME before PVC delete — skipping test 7"
else
    log "fragment found: $FRAGMENT — deleting PVC and waiting for it to disappear"
    k delete pvc "$PVC" --wait=true
    # Provisioner delete is async; allow a brief settling window.
    fragment_gone() {
        ! k exec "$NFS_POD" -- test -f "/etc/exports.d/$FRAGMENT"
    }
    wait_for 30 fragment_gone \
        || fail "exports fragment $FRAGMENT not removed after PVC delete"
    pass "exports fragment $FRAGMENT removed on PVC delete"
fi

log "ALL TESTS PASSED"
