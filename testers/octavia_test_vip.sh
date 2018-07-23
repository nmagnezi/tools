#!/usr/bin/env bash

VIP=10.0.0.11
QROUTER_NAMESPACE=qrouter-106278e1-2c9f-4e67-a2f0-84c02b58a584
LOG=$HOME/amp_test1.txt

while true ; do sudo ip netns exec $QROUTER_NAMESPACE curl $VIP | tee -a $LOG ; sleep 2 ; done
