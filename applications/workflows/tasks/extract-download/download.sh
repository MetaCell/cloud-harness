#!/bin/bash

set -e

# remove the pvc from the path (if it has one)
# and append the folder
export download_path=`echo $shared_directory | cut -d ":" -f 2`/"${folder}"

mkdir -p "${download_path}"
cd "${download_path}"

export filename=`echo "${url##*/}"`


filename=$(wget -nv --content-disposition  "$url" -P "${download_path}" 2>&1 |cut -d\" -f2)
echo "Downloaded to "$filename
# test if the download is a zip file, if so then extract and remove 
file "${filename}"|grep Zip && unzip "${filename}" && rm -f "${filename}"

# fix permissions
chown -R 1000:1000 "${download_path}"
