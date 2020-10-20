#!/bin/bash

# install deps in one venv for speed

module_dir=$(ls -d src/*)
python -m venv "${WORKDIR}/venv" 
source "$VENV_DIR"
pip install --cache-dir "${WORKDIR}/pip_cache" wheel coverage coverage-badge

for dir in $module_dir; do
  cd "$dir" || exit 1
  pip install --cache-dir "${WORKDIR}/pip_cache" -r requirements.txt
  cd ../.. || exit 1
done
