import urllib.request
import sys
from cloudharness import log
import os, stat
from pathlib import Path

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

log.info("Downloading {} to {}".format(url, dest))

urllib.request.urlretrieve(url, dest)

# test to see if the file is an zip archive
import mimetypes

mime = mimetypes.MimeTypes().guess_type(dest)[0]

mode_file = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH  # r+w g+o
mode_dir = mode_file | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH  # for dirs also execute
if mime == "application/zip":
    # extract it to the download_path folder
    import zipfile

    with zipfile.ZipFile(dest, 'r') as zip_ref:
        zip_ref.extractall(download_path)
        for fname in zip_ref.namelist():
            name = os.path.join(download_path, fname)
            if os.path.isdir(name):
                try:
                    os.chmod(name, mode_dir)
                except:
                    log.warning("Cannot change folder permissions: %s", name, exc_info=True)
            else:
                try:
                    # log.info(f"chmod {dirpath}/{filename} to {mode_file}")
                    os.chmod(name, mode_file)
                except:
                    log.warning("Cannot change file permissions: %s", name, exc_info=True)
    os.remove(dest)
else:
    try:
        os.chmod(dest, mode_file)
    except:
        log.warning("Cannot change file permissions: %s", dest, exc_info=True)

