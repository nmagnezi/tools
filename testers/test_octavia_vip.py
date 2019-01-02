#!/usr/bin/python
import netifaces as ni

from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.v2_0 import client as neutron
from octaviaclient.api.v2 import octavia


# Still a work in progress

ETH_NAME = 'eth0'
USER = 'admin'
PASS = 'admin'
PROJECT = 'admin'
REGION = 'RegionOne'

def get_nic_ip():
    return ni.ifaddresses(ETH_NAME)[ni.AF_INET][0]['addr']


def get_keystone_session(ip):
    auth = identity.v3.Password(
        auth_url='http://{}/identity/v3'.format(ip),
        username=USER,
        user_domain_name='default',
        password=PASS,
        project_name=PROJECT,
        project_domain_name='default')
    return session.Session(auth=auth)


def get_octviaclient(session, ip):
    return octavia.OctaviaAPI(
        session=session,
        endpoint='http://{}/load-balancer/v2.0/'.format(ip),
        service_type='load-balancer')


def get_neutron_client(session, ip):
    return neutron.Client(
        session=session,
        endpoint_url='http://{}:9696'.format(ip),
        service_type='network')


def main():
    import pdb ; pdb.set_trace()
    ip = get_nic_ip()
    session = get_keystone_session(ip)
    octavia_client = get_octviaclient(session, ip)
    neutron_client = get_neutron_client(session)

    neutron_client.list_networks()

    lbs = octavia_client.load_balancer_list()
    for lb in lbs['loadbalancers']:
        print lb


if __name__ == '__main__':
    main()





