#!/bin/bash

REMOTE_PATH="/opt/openstack/neutron/"
LOCAL_PATH="/git/neutron"

rsync --exclude=.tox --exclude=.idea --exclude=*.pyc --exclude=*.pyo --exclude=.venv -avzh --progress --delete root@$1:$REMOTE_PATH $LOCAL_PATH