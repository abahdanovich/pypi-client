#!/usr/bin/env bash

# Recreate `requirements.txt` file

set -e
set -o pipefail

cd "`dirname $0`"
cd ..

rm -rf .venv
poetry install
poetry run pip install -U pip
poetry run pip list \
  --format freeze \
  --exclude pip \
  --exclude wheel \
  --exclude setuptools \
  --exclude pypi-client > requirements.txt
