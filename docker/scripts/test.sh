#!/bin/bash

set -eou pipefail

# User the venv

source "$VENV_DIR"

# Run test and output to .coverage
coverage run -m unittest discover -s tests
