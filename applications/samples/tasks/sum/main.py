from cloudharness.workflows.utils import get_shared_directory
import sys
import os

assert len(sys.argv) > 2, 'Arguments not specified. Cannot proceed'


a = float(sys.argv[1])
b = float(sys.argv[2])

for env in os.environ:
    print(f"{env}:{os.environ[env]}")

file_name = os.path.join(get_shared_directory(), "result")
print("File name is", file_name)

with open(file_name, "w") as f:
    f.write(str(a + b))
