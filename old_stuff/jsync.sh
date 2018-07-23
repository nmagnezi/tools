#!/bin/bash

RSYNC="rsync --exclude=.tox --exclude=.idea --exclude=*.pyc
--exclude=*.pyo --exclude=*~ --exclude=.*.swp --exclude=.*.swo -azh
--progress --delete"

arg="$1"
ip="$2"

if [ -z $ip ]; then
    echo "Usage: rsync.sh <--to|--from> <ip>"
    exit
fi

# These directories are the *containing* directories
LOCAL_DIR="/home/nmagnezi/Dropbox/redhat/laptop/git/"
REMOTE_DIR="stack@$ip:/opt/openstack"

REPOS="neutron"

if [ $arg == "--to" ]; then
    for repo in $REPOS; do
        $RSYNC $LOCAL_DIR/$repo $REMOTE_DIR
    done
else
    for repo in $REPOS; do
        $RSYNC $REMOTE_DIR/$repo $LOCAL_DIR
    done
fi
