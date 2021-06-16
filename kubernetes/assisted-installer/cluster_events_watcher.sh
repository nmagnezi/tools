#!/usr/bin/env bash

ACI_NS=$1
ACI=$2
LINES=15

eventsURL=$(kubectl -n $ACI_NS get agentclusterinstall $ACI -o=jsonpath="{.status.debugInfo.eventsURL}")
watch -d "curl -s -k $eventsURL | jq "." | tail -${LINES}f"
