# My Scripts

## Dev Helpers
* [Sync code between machines](development/codesync.md)
* [Devstack Configurations](devstack_configs)
* [Prep a cloud VM for devstack](development/devstack_install.sh) 

> `curl https://raw.githubusercontent.com/nmagnezi/scripts/master/development/devstack_install.sh  > devstack_install.sh ; bash devstack_install.sh`

## Git tools
* [Git Global Configuration](git/git_prep.sh)

## Tester scripts

### Octavia
* [Amphorae State](test/octavia_amp_ha.sh)
* [Test VIP](octavia_test_vip.sh)

### Octavia or Neutron-LBaaS
* [Create Loadbalancer and HTTP servers for testing](test_lb.sh)

### Other testers
* [Scapy](testers/scapy_script.py)
* [PyOpenSSL](testers/test_pyopenssl.py)
