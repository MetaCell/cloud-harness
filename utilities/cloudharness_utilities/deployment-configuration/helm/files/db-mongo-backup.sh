#!/bin/bash

set -e
set -u

KEEP_DAYS=${BACKUP_KEEP_DAYS}
KEEP_WEEKS=`expr $(((${BACKUP_KEEP_WEEKS} * 7) + 1))`
KEEP_MONTHS=`expr $(((${BACKUP_KEEP_MONTHS} * 31) + 1))`

mkdir -p "${BACKUP_DIR}/daily/" "${BACKUP_DIR}/weekly/" "${BACKUP_DIR}/monthly/"

# Clean old files
echo "Cleaning backups older than ${KEEP_DAYS} ..."
find "${BACKUP_DIR}/daily" -maxdepth 1 -mtime +${KEEP_DAYS} -name "*${BACKUP_SUFFIX}" -print -delete
find "${BACKUP_DIR}/weekly" -maxdepth 1 -mtime +${KEEP_WEEKS} -name "*${BACKUP_SUFFIX}" -print -delete
find "${BACKUP_DIR}/monthly" -maxdepth 1 -mtime +${KEEP_MONTHS} -name "*${BACKUP_SUFFIX}" -print -delete

DFILE="${BACKUP_DIR}/daily/`date +%Y-%m-%d-%H%M%S`${BACKUP_SUFFIX}"
WFILE="${BACKUP_DIR}/weekly/`date +%G-%V`${BACKUP_SUFFIX}"
MFILE="${BACKUP_DIR}/monthly/`date +%Y-%m`${BACKUP_SUFFIX}"

# Dump mongo database
/usr/bin/mongodump -h $DB_HOST -u $DB_USER -p $DB_PASS --archive=$DFILE --gzip

# Use hardlink instead of copy to save space
if [ -d "${DFILE}" ]; then
    WFILENEW="${WFILE}-new"
    MFILENEW="${MFILE}-new"
    rm -rf "${WFILENEW}" "${MFILENEW}"
    mkdir "${WFILENEW}" "${MFILENEW}"
    ln -f "${DFILE}/"* "${WFILENEW}/"
    ln -f "${DFILE}/"* "${MFILENEW}/"
    rm -rf "${WFILE}" "${MFILE}"
    mv -v "${WFILENEW}" "${WFILE}"
    mv -v "${MFILENEW}" "${MFILE}"
else
    ln -vf "${DFILE}" "${WFILE}"
    ln -vf "${DFILE}" "${MFILE}"
fi