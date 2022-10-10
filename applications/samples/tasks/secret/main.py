import os

from cloudharness.auth import get_api_password
from cloudharness.workflows.utils import get_shared_directory

for env in os.environ:
    print(f"{env}:{os.environ[env]}")

file_name = os.path.join(get_shared_directory(), "result")
print("File name is", file_name)

with open(file_name, "w") as f:
    f.write(get_api_password())
