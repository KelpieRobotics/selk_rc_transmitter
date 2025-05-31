#!/usr/bin/env bash

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# TODO: install protobuf

# Update all submodules
git submodule update --init

# Build msgs
source ${REPO_DIR}/selk_rc_msgs/scripts/build_msgs.sh

# Build Xpano
cd ./xpano
sudo apt install -y libgtk-3-dev libopencv-dev libsdl2-dev libspdlog-dev cmake gcc g++ python3 python3-pip
./misc/build/build-ubuntu-22.sh

cd ./build

export XPANO="$(pwd)/Xpano"
pip install pillow

cd ..
cd ..