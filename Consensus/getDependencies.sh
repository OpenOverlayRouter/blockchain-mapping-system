#!/bin/bash
set -euo pipefail

#---------------------------------------
# VARS
#---------------------------------------
dir="$(dirname $0)/../../bls"


#---------------------------------------
# MAIN
#---------------------------------------

if [ ! -d "$dir" ]; then
  # Download bls
  git clone https://github.com/janmroca/bls.git "$dir"

fi

# Set dev branch
cd "$dir"
git checkout dev

# Get bls dependencies
./getDependencies.sh

# Build bls
make sample_test

# Move lib
cd -
cp "$dir"/bin/bls_smpl.exe "$(dirname $0)"/utils/bls.exe
