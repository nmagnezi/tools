#!/usr/bin/env bash

yum install -y vim openstack-neutron-lbaas openstack-utils

# For OSP9 and below
#  neutron-db-manage --service lbaas --config-file /etc/neutron/neutron.conf --config-file /etc/neutron/plugins/ml2/ml2_conf.ini upgrade head
# For OSP10 and above
neutron-db-manage --subproject neutron-lbaas --config-file /etc/neutron/neutron.conf --config-file /etc/neutron/plugins/ml2/ml2_conf.ini upgrade head

crudini --set /etc/neutron/neutron_lbaas.conf service_providers service_provider "LOADBALANCERV2:Haproxy:neutron_lbaas.drivers.haproxy.plugin_driver.HaproxyOnHostPluginDriver:default"
n_plugins=$(crudini --get /etc/neutron/neutron.conf DEFAULT service_plugins)
n_plugins+=",neutron_lbaas.services.loadbalancer.plugin.LoadBalancerPluginv2"
crudini --set /etc/neutron/neutron.conf DEFAULT service_plugins $n_plugins
crudini --set /etc/neutron/lbaas_agent.ini DEFAULT ovs_use_veth False
crudini --set /etc/neutron/lbaas_agent.ini DEFAULT interface_driver "neutron.agent.linux.interface.OVSInterfaceDriver"
crudini --set /etc/neutron/services_lbaas.conf haproxy user_group haproxy

systemctl enable neutron-lbaasv2-agent.service
systemctl start neutron-lbaasv2-agent.service
systemctl restart neutron-server.service

source /root/keystonerc_admin
neutron agent-list



