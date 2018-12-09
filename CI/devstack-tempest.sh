#!/bin/bash
# Jenkins Job
##yes | ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa

# Copy key
sshpass -p ${password} ssh-copy-id -i ~/.ssh/id_rsa.pub ${username}@${ip_address}

# Get tox command
if [ -z "$tests" ]; then
   cmd=$(python tools/gen_tempest_runner.py --directory ${directory})
else
   cmd=$(python tools/gen_tempest_runner.py --tests ${tests} --directory ${directory})
fi


# Put tox command into a script
chmod +x tempest.sh

# Copy runner script
scp -p tempest.sh ${username}@${ip_address}:${directory}/

ssh root@${ip_address} "cd /opt/openstack/tempest && ${directory}/tempest.sh"


# Collect results
scp ${username}@${ip_address}:${directory}/tempest.log .
scp ${username}@${ip_address}:${directory}/xunit.xml .
