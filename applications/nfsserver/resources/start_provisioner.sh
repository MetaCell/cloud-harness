#!/bin/bash

echo Starting provisioner...
while true; do
    /usr/local/bin/nfs-subdir-external-provisioner
    sleep 1
done
echo Starting provisioner done.
