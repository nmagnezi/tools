#!/usr/bin/env bash

# Test VIP traffic while monitoring the amps list

VIP=10.0.0.11
QROUTER_NAMESPACE=qrouter-106278e1-2c9f-4e67-a2f0-84c02b58a584

LOG=$HOME/amp_test1.txt
VIP_COMMAND="timeout 1s sudo ip netns exec "$QROUTER_NAMESPACE" curl "$VIP""
QROUTER_NS_VIP_MAC_COMMAND=$(sudo ip netns exec "$QROUTER_NAMESPACE" arp -a | awk '/'$VIP'/ {print $2" "$3" "$4" "$7" "$8}')

touch $LOG
echo "" > $LOG
while true; do
	echo "" | tee -a $LOG
	date | tee -a $LOG
	#if $VIP_COMMAND ; then
	#    echo "VIP '$VIP' Responding" | tee -a $LOG
	#else
	#    echo "VIP '$VIP' Not Responding" | tee -a $LOG
	#fi

  # this is blocking when it does not work, so instead I used:
  # while true ; do date ; curl 10.0.0.11 | tee -a /opt/stack/amp_test1.txt ; sleep 2 ; done
  # Probably there's a better solution for this.

	echo $QROUTER_NS_VIP_MAC_COMMAND | tee -a $LOG
	openstack loadbalancer amphora list | tee -a $LOG
	sleep 4
done