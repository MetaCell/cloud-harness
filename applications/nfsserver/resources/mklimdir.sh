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
    set -x

    option_handler(){

        case ${opt} in
            m) mountpoint=${OPTARG} ;;
            s) size=${OPTARG} ;;
            h) print_usage; exit 0 ;;
            \?) echo ">>>Invalid option: -$OPTARG" > /dev/stderr; exit 1;;
            \:) echo ">>>Missing argument to -${OPTARG}" > /dev/stderr; exit 2;;
        esac
    }

    local OPTIND opt
    getopts "m:s:f:h" opt || { echo "No args passed">/dev/stderr;print_usage;exit 3;}
    option_handler 
    while getopts "m:s:h" opt; do
         option_handler
    done
    shift $((OPTIND-1))

}


main(){
    if [ $EUID -ne 0 ]; then
        echo ">>> Please run the script with sudo/as root" > /dev/stderr
        exit 4
    fi

    local mountpoint=""
    local size=0

    parse_args "$@"
    quota_fs=${mountpoint}.quota

    losetup -a|grep ${mountpoint}|awk '{print $1}'|cut -f 1 -d :|xargs losetup -d || true

    i=1
    while [ -e /dev/loop${i} ]; do i=$(( i+1 )); done
    # lodev=`losetup -f`
    lodev=/dev/loop${i}

    # truncate -s ${size} ${quota_fs}
    count_mb=$(( ${size}/1024/1024 + 1))
    dd if=/dev/zero of=${quota_fs} bs=1M count=${count_mb}
    yes | mkfs.ext4 ${quota_fs}

    mknod -m666 ${lodev} b 7 ${i} || true
    losetup -P ${lodev} ${quota_fs}

    rm -rf ${mountpoint}
    mkdir ${mountpoint}
    chmod go+w ${mountpoint}
    mount -o loop ${lodev} ${mountpoint}
    chmod go+w ${mountpoint}
}

main "$@"
