#!/usr/bin/env bash

export HOST_IP=10.1.2.3
export MINIKUBE_IP=192.168.39.61
export PORT=8080

iptables -t nat -I PREROUTING -p tcp -d $HOST_IP --dport $PORT -j DNAT --to-destination $MINIKUBE_IP:$PORT
iptables -I FORWARD -p tcp -m tcp --sport $PORT -j ACCEPT
iptables -I FORWARD -p tcp -m tcp --dport $PORT -j ACCEPT

