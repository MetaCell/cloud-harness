#!/usr/bin/env bash
# Author: Zoran Sinnema
# Date: 14-11-2022


# example of resizing a mounted pvc:
# dd if=/dev/zero bs=1MiB of=/export/<filename.quota> conv=notrunc oflag=append count=<num blocks to add>

set -e

print_usage(){

cat <<EOF
Usage: mklimdir.sh -m <Mountpoint Directory> -s <INT>

-m directory
-s size in bytes
-mo mount only
-h this message

Exit statuses:
0:
1: Invalid option
2: Missing argument
3: No args
4: root privillege required
EOF
} > /dev/stderr

parse_args(){
    options=$(getopt -l "h,m:,s:,mountonly" -o "hm:s:" -a -- "$@")
    eval set -- "$options"
    while true
    do
    case "$1" in
    -h)
        print_usage; exit 0 ;;
    -m)
        shift; export mountpoint="$1" ;;
    -s)
        shift; export size="$1" ;;
    --mountonly)
        export mountonly=1 ;;
    --)
        shift
        break;;
    esac
    shift
    done
}

unmount(){
    mountpoint=$1
    echo Unmount ${mountpoint}
    for lodev in $(losetup -a|grep ${mountpoint}|awk '{print $1}'|cut -f 1 -d :); do
        losetup -d ${lodev}|| true
    done
}

mkmount(){
    mountpoint=$1
    quota_fs=$2

    unmount "${mountpoint}"

    echo Mounting ${quota_fs} on ${mounpoint}
    i=$(losetup -f|cut -f 2 -d p)
    lodev=/dev/loop${i}

    mknod -m666 ${lodev} b 7 ${i} 2>/dev/null || true
    losetup -P ${lodev} ${quota_fs}

    rm -rf ${mountpoint}
    mkdir ${mountpoint}
    # chmod go+w ${mountpoint}
    chmod 777 ${mountpoint}
    mount ${lodev} ${mountpoint}
    # chmod go+w ${mountpoint}
    chmod 777 ${mountpoint}
}

mklimfile(){
    quota_fs=$1
    size=$2
    count_mb=$(( ${size}/1024/1024 + 1))

    echo Create file ${quota_fs} size ${count_mb}Mb
    truncate -s ${size} ${quota_fs}
    #dd if=/dev/zero of=${quota_fs} bs=1M count=${count_mb}
    yes | mkfs.ext4 ${quota_fs}
}

main(){
    if [ $EUID -ne 0 ]; then
        echo ">>> Please run the script with sudo/as root" > /dev/stderr
        exit 4
    fi

    local mountpoint=""
    local size=0
    local mountonly=

    parse_args "$@"
    quota_fs=${mountpoint}.quota

    if [ -z ${mountonly} ]; then
        if [ -f ${quota_fs} ]; then
            echo File ${quota_fs} already exists
            exit 1
        fi
        mklimfile "${quota_fs}" "${size}"
    fi
    mkmount "${mountpoint}" "${quota_fs}"
}

main "$@"
