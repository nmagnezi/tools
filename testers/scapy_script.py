#! /usr/bin/env python

from scapy.all import *

p = (Ether(src="f1:23:45:67:89:00", dst="ff:ff:ff:ff:ff:ff")
     /IP(src="169.254.192.1", dst="224.0.0.18"))
sendp(p, iface="br-tun")
