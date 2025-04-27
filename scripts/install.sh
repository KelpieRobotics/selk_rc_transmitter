#!/usr/bin/env bash

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# TODO: install protobuf

# Update all submodules
git submodule update --init

# Build msgs
source ${REPO_DIR}/selk_rc_msgs/scripts/build_msgs.sh
