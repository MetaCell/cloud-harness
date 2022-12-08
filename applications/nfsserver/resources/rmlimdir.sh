#!/usr/bin/env bash
# Author: Zoran Sinnema
# Date: 14-11-2022

print_usage(){

cat <<EOF
Usage: rmlimdir.sh -m <Mountpoint Directory>

-m directory
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
            h) print_usage; exit 0 ;;
            \?) echo ">>>Invalid option: -$OPTARG" > /dev/stderr; exit 1;;
            \:) echo ">>>Missing argument to -${OPTARG}" > /dev/stderr; exit 2;;
        esac
    }

    local OPTIND opt
    getopts "m:s:f:h" opt || { echo "No args passed">/dev/stderr;print_usage;exit 3;}
    option_handler 
    while getopts "m:h" opt; do
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

    parse_args "$@"
    quota_fs=${mountpoint}.quota
    mountname=`basename ${mountpoint}`

    # find the loop back device and delete/unmount it
    lodev=`losetup -a | grep ${mountname} | awk '{print $1}' | cut -f 1 -d :` || true

    losetup -d ${lodev} || true
    umount -df ${mountpoint} || true

    rm -rf ${mountpoint} || true
    mv ${quota_fs} ${mountpoint} || true

}

main "$@"
