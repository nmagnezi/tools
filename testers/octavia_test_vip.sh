#!/usr/bin/env bash

LB_NAME="lb1"
ROUTER_NAME="router1"
LOG=$HOME/amp_test1.txt
SLEEP=2
source $HOME/devstack/openrc admin admin
VIP=$(openstack loadbalancer show "$LB_NAME" -f value -c vip_address)
ROUTER_ID=$(openstack router show "$ROUTER_NAME" -f value -c id)
QROUTER_NAMESPACE="qrouter-"$ROUTER_ID

while true ; do sudo ip netns exec $QROUTER_NAMESPACE curl $VIP | tee -a $LOG ; sleep $SLEEP ; done
