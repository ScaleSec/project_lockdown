#!/bin/bash

set -eou pipefail

# User the venv

source "$VENV_DIR"

# Run test and output to .coverage
coverage run -m unittest discover -s tests

# Generage SVG badge which is embedded in readme
coverage-badge -f -q -o coverage/.coverage
