#!/bin/bash

set -Eeou pipefail

# you can do secrets pulling and other startup logic here

# todo: use a volume in the container to mount the whole src so we don't have to rebuild and reinstall

# Install deps, put here so we can use a local bind to cache pip otherwise building this will take 15 minutes each time
/usr/local/bin/install_deps.sh

# Start app 
if [[ "$1" == *"test"* ]]; then
  exec /usr/local/bin/test.sh
else
  exec "$@"
fi