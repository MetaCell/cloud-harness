import urllib.request
import sys
import logging
import os, stat
from pathlib import Path

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

assert len(sys.argv) > 2, 'Arguments not specified. Cannot download'

url = sys.argv[1]
download_path = sys.argv[2].split(':')[-1]

if len(sys.argv) == 4:
    folder = sys.argv[3]
else:
    folder = "."

download_path = os.path.join(download_path, folder)
Path(download_path).mkdir(parents=True, exist_ok=True)

dest = os.path.join(download_path, url.split('/')[-1])

logging.info("Downloading {} to {}".format(url, dest))

urllib.request.urlretrieve(url, dest)

# test to see if the file is an zip archive
import mimetypes
mime = mimetypes.MimeTypes().guess_type(dest)[0]
if mime == "application/zip":
    # extract it to the download_path folder
    import zipfile
    with zipfile.ZipFile(dest, 'r') as zip_ref:
        zip_ref.extractall(download_path)
        os.remove(dest)

# TODO: may be a bit too drastic, may be only change the destination but how to handle the zip files where if there is a folder it is unknow
mode_file = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH # r+w g+o
mode_dir = mode_file | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH # for dirs also execute
for dirpath, dirnames, filenames in os.walk(download_path):
    os.chmod(dirpath, mode_dir)
    for filename in filenames:
        os.chmod(os.path.join(dirpath, filename), mode_file)
        logging.info(f"chmod {dirpath}/{filename} to {mode_file}")
