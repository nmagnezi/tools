#!/bin/bash

# Just the basics of setting a cloud image based instance to be ready for devstack
# To Copy & Run:
# curl https://raw.githubusercontent.com/nmagnezi/scripts/master/development/devstack_install.sh  > devstack_install.sh ; bash devstack_install.sh

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Determine which OS
export SERVER_OS=$(awk -F "=" '/^NAME/ {print $2}' /etc/*-release)


if [[ "$SERVER_OS" == '"CentOS Linux"' ]]; then
    export USER="centos"
elif [[ "$SERVER_OS" == '"Red Hat Enterprise Linux Server"' ]]; then
    export USER="cloud-user"
else
    # "Ubuntu"
    export USER="ubuntu"
fi

# set locale if logged in from macOS
echo "LANG=en_US.UTF-8" >> /etc/environment
echo "LC_ALL=en_US.UTF-8" >> /etc/environment

# create and set stack user as sudoer
useradd -s /bin/bash -d /opt/stack -m stack
echo "stack ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/stack

# Copy the injected ssh keys to the stack user, for direct SSH access
mkdir /opt/stack/.ssh
cp /home/$USER/.ssh/authorized_keys /opt/stack/.ssh
chown -R stack:stack /opt/stack/.ssh/
chmod 700 /opt/stack/.ssh
chmod 600 /opt/stack/.ssh/authorized_keys

# Install git and tools
yum install -y vim git tig wget || apt-get install -y vim git tig wget

# Clone my scripts
sudo -u stack sudo git clone https://github.com/nmagnezi/scripts.git /opt/stack/scripts
chown -R stack:stack /opt/stack/scripts


sudo -u stack sudo git clone https://git.openstack.org/openstack-dev/devstack /opt/stack/devstack
chown -R stack:stack /opt/stack/devstack


echo ""
echo "Now create your local.conf and stack"
echo ""

