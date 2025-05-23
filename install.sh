#!/usr/bin/env bash
CURRENT_PATH=$(pwd)

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $SCRIPT_DIR
pip install --upgrade pip
cat requirements.txt
pip install -r requirements.txt

cd $CURRENT_PATH