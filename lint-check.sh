#!/bin/bash
# Run autopep8 with --diff and capture the output
diff_output=$(python -m autopep8 --select=E1,E2,E3,W,E4,E7,E502  --recursive --diff --exclude '**/cloudharness_cli/**/*,**/models/*,**/model/*' .)
# Check if the output is non-empty
if [ -n "$diff_output" ]; then
    printf "%s\n" "$diff_output"
    echo "Code style issues found in the above files. To fix you can run: "
    echo "autopep8 --select=E1,E2,E3,W,E4,E7,E502  --recursive  --in-place --exclude '**/cloudharness_cli/**/*,**/models/*,**/model/*'"
    exit 1
fi