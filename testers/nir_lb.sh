#!/usr/bin/env bash

su - stack
. openrc admin demo
subnet_name="private-subnet"
lb_name="test_lb1"
lb_listener_name="test_lb1_listener"
pool_name="test_lb1_pool"
node1="node1"
node2="node2"
BOOT_DELAY=60
TOP_DIR=$(cd $(dirname "$0") && pwd)

# Create an SSH key to use for the instances
DEVSTACK_LBAAS_SSH_KEY_NAME=$(hostname)_DEVSTACK_LBAAS_SSH_KEY_RSA
DEVSTACK_LBAAS_SSH_KEY_DIR=${TOP_DIR}
DEVSTACK_LBAAS_SSH_KEY=${DEVSTACK_LBAAS_SSH_KEY_DIR}/${DEVSTACK_LBAAS_SSH_KEY_NAME}
rm -f ${DEVSTACK_LBAAS_SSH_KEY}.pub ${DEVSTACK_LBAAS_SSH_KEY}
ssh-keygen -b 2048 -t rsa -f ${DEVSTACK_LBAAS_SSH_KEY} -N ""
nova keypair-add --pub_key=${DEVSTACK_LBAAS_SSH_KEY}.pub ${DEVSTACK_LBAAS_SSH_KEY_NAME}


lb_subnet=`neutron subnet-show $subnet_name | awk '/ id/ {print $4}'`
neutron lbaas-loadbalancer-create $lb_subnet --name $lb_name
lb_id=`neutron lbaas-loadbalancer-show $lb_name | awk '/ id/ {print $4}'`
neutron lbaas-listener-create --name $lb_listener_name --loadbalancer $lb_id --protocol HTTP --protocol-port 80
listener_id=`neutron lbaas-listener-show $lb_listener_name | awk '/ id/ {print $4}'`
neutron lbaas-pool-create --lb-algorithm ROUND_ROBIN --listener $listener_id --protocol HTTP --name $pool_name
pool_id=`neutron lbaas-pool-show $pool_name | awk '/ id/ {print $4}'`

image_name="cirros-0.3.4-x86_64-uec"
boot_args="--key-name ${DEVSTACK_LBAAS_SSH_KEY_NAME} --image $(glance image-show $image_name | awk '/ id/ {print $4}') --flavor 1 --nic net-id=$(neutron subnet-show $lb_subnet | awk '/network_id/ {print $4}')"

nova boot $node1 $boot_args
nova boot $node2 $boot_args


echo "Waiting ${BOOT_DELAY} seconds for instances to boot"
sleep ${BOOT_DELAY}


node1_ip=$(nova show $node1 | awk '/private network/ {print $5}' | cut -d"," -f 1)
node2_ip=$(nova show $node2 | awk '/private network/ {print $5}' | cut -d"," -f 1)

ssh-keygen -R $node1_ip
ssh-keygen -R $node1_ip

# Run a simple web server on the instances
scp -i ${DEVSTACK_LBAAS_SSH_KEY} -o StrictHostKeyChecking=no ${TOP_DIR}/webserver.sh cirros@${node1_ip}:webserver.sh
scp -i ${DEVSTACK_LBAAS_SSH_KEY} -o StrictHostKeyChecking=no ${TOP_DIR}/webserver.sh cirros@${node1_ip}:webserver.sh



neutron lbaas-member-create --subnet private-subnet --address $node1_ip --protocol-port 80 $pool_id
neutron lbaas-member-create --subnet private-subnet --address $node2_ip --protocol-port 80 $pool_id


# Add tcp/22,80 and icmp to default security group
nova secgroup-add-rule default tcp 22 22 0.0.0.0/0
nova secgroup-add-rule default tcp 80 80 0.0.0.0/0
nova secgroup-add-rule default icmp -1 -1 0.0.0.0/0


ssh -i ${DEVSTACK_LBAAS_SSH_KEY} -o StrictHostKeyChecking=no cirros@${IP1} ./webserver.sh
ssh -i ${DEVSTACK_LBAAS_SSH_KEY} -o StrictHostKeyChecking=no cirros@${IP2} ./webserver.sh
