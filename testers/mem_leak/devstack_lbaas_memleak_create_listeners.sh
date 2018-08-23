#!/usr/bin/env bash

LB_NAME="lb_"$RANDOM
MEM_CHECK_INTERVAL=10

source /root/keystonerc_admin

echo "Before we created a loadbalancer" > mem_usage.txt
/root/memexplore.py all neutron-server | grep Total | awk '{print $3}' >> mem_usage.txt

neutron lbaas-loadbalancer-create --name $LB_NAME private_subnet
sleep 5
echo "After we created a loadbalancer" >> mem_usage.txt
/root/memexplore.py all neutron-server | grep Total | awk '{print $3}' >> mem_usage.txt

echo "Starting to create listeners"

for i in `seq 1 1000`
do
  neutron lbaas-listener-create --loadbalancer $LB_NAME --protocol HTTP --protocol-port $i --name listener_$i -c name --format value >> mem_usage.txt
  # Check memory usage for each $MEM_CHECK_INTERVAL created listeners
  if (( i % $MEM_CHECK_INTERVAL == 0 ))
  then
  /root/memexplore.py all neutron-server | grep Total | awk '{print $3}' >> mem_usage.txt
  fi
  sleep 3
done
