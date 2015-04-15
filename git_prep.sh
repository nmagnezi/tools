#!/bin/bash

# Pre a devstack node for gerrit.
# Based on: http://docs.openstack.org/infra/manual/developers.html

FULL_NAME="Nir Magnezi"
EMAIL="nmagnezi@redhat.com"

git config --global user.name $FULL_NAME
git config --global user.email $EMAIL

# Installing git-review
yum install git-review

# Accessing Gerrit over HTTPS
git config --global gitreview.scheme https
git config --global gitreview.port 443

#print config
git config --list