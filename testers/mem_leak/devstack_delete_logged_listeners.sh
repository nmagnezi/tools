#!/usr/bin/env bash

# delete listeners logged to mem_usage.txt

MEM_CHECK_INTERVAL=10
source /opt/stack/devstack/openrc admin admin


echo "Before we delete a listeners" > mem_usage_listener_delete.txt
./memexplore.py all neutron-server | grep Total | awk '{print $3}' >> mem_usage_listener_delete.txt


LOOP_INTERVAL=0
for i in `grep listener_ mem_usage.txt`
do
  LOOP_INTERVAL=$((LOOP_INTERVAL+1))
  neutron lbaas-listener-delete $i >> mem_usage_listener_delete.txt
  if (( $LOOP_INTERVAL % $MEM_CHECK_INTERVAL == 0 ))
  then
  ./memexplore.py all neutron-server | grep Total | awk '{print $3}' >> mem_usage_listener_delete.txt
  fi
  sleep 3
done
