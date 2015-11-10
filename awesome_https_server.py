# based on:
# 1. http://www.piware.de/2011/01/creating-an-https-server-in-python/
# 2. http://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-of-eth0-in-python

# how to generate server.pem:
#   openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes

# how to run:
#   sudo python awesome_https_server.py -n enp0s25
# how to test:
#   curl https://<ip_address>:443 --insecure

import BaseHTTPServer
import SimpleHTTPServer
import argparse
import fcntl
import socket
import ssl
import struct


def get_nic():
    parser = argparse.ArgumentParser(description='Awesome HTTPS server')
    parser.add_argument('-n', '--nic',
                        help='NIC that holds the server IP address',
                        required=False, default='eth0')

    return parser.parse_args().nic


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def start_https_server(ip_address):
    httpd = BaseHTTPServer.HTTPServer((ip_address, 443),
                                      SimpleHTTPServer.SimpleHTTPRequestHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./server.pem',
                                   server_side=True)
    httpd.serve_forever()


def main():
    nic = get_nic()
    ip_address = get_ip_address(nic)
    start_https_server(ip_address)

if __name__ == '__main__':
    main()
