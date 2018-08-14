#!/usr/bin/env bash

# 1. Builds an amphora image from local code found on the disk
# 2. Upload it to glance and tag with "amphora"

export AMP_OS_FLAVOR="centos"
export AMP_DISK_SIZE="3"
export PROJECT_NAME="admin"
export TOP_DIR="/opt/stack/devstack"

# For diskimage-builder
export OCTAVIA_DIR="/opt/stack/octavia"
export DIB_REPOLOCATION_amphora_agent=$OCTAVIA_DIR
export DIB_REPOREF_amphora_agent=$(git --git-dir="$OCTAVIA_DIR/.git" log -1 --pretty="format:%H")


pushd $OCTAVIA_DIR/diskimage-create
./diskimage-create.sh -i $AMP_OS_FLAVOR -s $AMP_DISK_SIZE

source ${TOP_DIR}/openrc ${PROJECT_NAME} ${PROJECT_NAME}
openstack image create local_centos_amp --file /opt/stack/octavia/diskimage-create/amphora-x64-haproxy.qcow2 --tag amphora --disk-format qcow2 --container-format bare
popd
