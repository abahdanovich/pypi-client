#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`"
cd ..

poetry run pytest pypi_client/ tests/
