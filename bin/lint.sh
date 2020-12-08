#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`"
cd ..

poetry run pylint pypi_client/ tests/
poetry run mypy pypi_client/ tests/
