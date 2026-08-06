#!/bin/bash

# Copyright 2015 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

function start()
{
    # Start the HTTP liveness server immediately, then run mount-all inside the
    # watchdog process. /healthz returns 200 at once (liveness probe satisfied);
    # /ready returns 200 only once mount-all finishes (readiness gate).
    /usr/local/bin/nfsvol watchdog -mount-first &

    bash -c "/usr/local/bin/start_provisioner.sh&"

    unset gid
    # accept "-G gid" option
    while getopts "G:" opt; do
        case ${opt} in
            G) gid=${OPTARG};;
        esac
    done
    shift $(($OPTIND - 1))

    # start rpcbind if it is not started yet
    /usr/sbin/rpcinfo 127.0.0.1 > /dev/null; s=$?
    if [ $s -ne 0 ]; then
       echo "Starting rpcbind"
       /usr/sbin/rpcbind -w
    fi

    mount -t nfsd nfsd /proc/fs/nfsd

    # rpc.mountd: no -V flag — let it register all mount protocol versions (1,2,3).
    # Adding -V 3 here incorrectly restricts registration to version 1 only,
    # which causes "Permission denied" on NFSv3 client mounts.
    /usr/sbin/rpc.mountd

    /usr/sbin/exportfs -r
    # -G 10 to reduce grace time to 10 seconds (the lowest allowed).
    # -V 3: enable NFSv3 (matches client mount options).
    /usr/sbin/rpc.nfsd -G 10 -V 3
    /usr/sbin/rpc.statd --no-notify
    echo "NFS started"
}

function stop()
{
    echo "Stopping NFS"

    /usr/sbin/rpc.nfsd 0
    /usr/sbin/exportfs -au
    /usr/sbin/exportfs -f

    kill $( pidof rpc.mountd ) 2>/dev/null || true
    umount /proc/fs/nfsd

    # Lazy-unmount all loop-backed exports before exiting. The pod shares the
    # host mount namespace, so any mount left alive here persists after the
    # container dies. The next pod's LOOP_CLR_FD then fails with EBUSY and
    # cannot reuse the loop device.
    for mp in /exports/*/; do
        umount -l "$mp" 2>/dev/null || true
    done

    echo > /etc/exports
    exit 0
}


# rpc.statd has issues with very high ulimits
ulimit -n 65535

# Each loop device creates inotify watches inside the container. On deployments
# with thousands of PVCs the kernel default (8192-12288) is exhausted, which
# causes rpc.mountd to fail with "No space left on device". Write directly to
# /proc/sys rather than using sysctl(8), which is not installed in this image.
# The pod is privileged so the write is permitted.
echo 1048576 > /proc/sys/fs/inotify/max_user_watches  2>/dev/null || true
echo 8192    > /proc/sys/fs/inotify/max_user_instances 2>/dev/null || true

# Self-heal: the kernel nfsd can die (threads -> 0) while rpcbind, mountd, the
# export table and the provisioner all stay up — leaving NFS silently not
# serving on :2049 with the watchdog's /healthz still green. (Observed: the pod
# sat 0/1 for ~42h with nfsd threads=0 while everything else looked fine.)
# Restart nfsd IN PLACE: the exports and the thousands of volume mounts are
# still intact, so this recovers in seconds — far cheaper than a pod restart,
# which would remount every volume. The liveness probe on :2049 is the backstop
# if this ever fails to bring nfsd back.
function ensure_nfsd()
{
    local threads
    threads=$(cat /proc/fs/nfsd/threads 2>/dev/null || echo 0)
    if [ "${threads:-0}" -eq 0 ]; then
        echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ'): nfsd down (threads=0) — restarting in place"
        /usr/sbin/exportfs -r
        /usr/sbin/rpc.nfsd -G 10 -V 3
    fi
}

trap stop TERM

start "$@"

# Keep the container alive and self-heal nfsd. Short sleeps keep SIGTERM (trap
# stop) responsive while still checking nfsd roughly every 15s.
while true; do
    ensure_nfsd
    sleep 15
done
