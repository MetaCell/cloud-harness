#!/bin/bash

# remount
losetup -D
for lodev in `losetup -a|grep deleted|awk '{print $1}'|cut -f 1 -d :`
do
    losetup -d ${lodev}
done

for qf in `ls /exports/*.quota`
do
    mountpoint=${qf%.*}
    mklimdir.sh -m ${mountpoint} --mountonly
done
