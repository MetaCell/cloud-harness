import urllib.request
import sys
import logging
import os

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

assert len(sys.argv) > 2, 'Arguments not specified. Cannot download'

url = sys.argv[1]
download_path = sys.argv[2]

dest = os.path.join(download_path, url.split('/')[-1])
logging.info("Downloading {} to {}".format(url, dest))

urllib.request.urlretrieve(url, dest)
