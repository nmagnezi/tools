#!/usr/bin/env bash

ACI_NS=$1
ACI=$2
LINES=15

while true; do
	kubectl -n $ACI_NS get agentclusterinstall $ACI -o=jsonpath="{.metadata.name}{'\n'}{range .status.conditions[*]}{.type}{'\t'}{'\t'}{.message}{'\n'}"
sleep 2
done
