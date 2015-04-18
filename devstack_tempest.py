#!/usr/bin/env python

import argparse
import logging
import paramiko
import sshutils

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
console = logging.StreamHandler()
LOG.addHandler(console)

SSH_TIMEOUT = 2
USERNAME = 'root'
PASSWORD = 'password'
TESTENV = 'all'
TEMPEST_DIRECTORY = "/opt/openstack/tempest"


class SSH(object):
    def __init__(self, args):
        self.ssh = paramiko.SSHClient()
        self.args = args

    def open_connection(self):
        self.ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        self.ssh.connect(hostname=self.args.ip_address,
                         username=self.args.username,
                         password=self.args.password,
                         timeout=SSH_TIMEOUT)

    def run_bash_command(self, bash_command):
        _, ssh_stdout, _ = self.ssh.exec_command("hostname")
        prompt = ("%(user)s@%(host)s tempest" %
                  {"user": self.args.username,
                   "host": (ssh_stdout.read()).strip().split(".")[0]})
        channel = self.ssh.invoke_shell()
        channel.send(bash_command + '\n')

        buffer = ''
        while buffer.find(prompt) < 0:
            response = channel.recv(9999)
            buffer += response
            print(response)

def process_args():
    parser = argparse.ArgumentParser(description='Tempest runner for Devstack')

    parser.add_argument('-i', '--ip_address',
                        help='Devstack IP Address', required=True)
    parser.add_argument('-u', '--username',
                        help='Devstack username for SSH', required=False,
                        default=USERNAME)
    parser.add_argument('-p', '--password',
                        help='Devstack password for SSH', required=False,
                        default=PASSWORD)
    parser.add_argument('-e', '--env',
                        help='tox environment', required=False,
                        default=TESTENV)
    parser.add_argument('-t', '--testr',
                        help='testr additional parameters', required=False)
    parser.add_argument('-d', '--directory',
                        help='Tempest directory', required=False,
                        default=TEMPEST_DIRECTORY)

    return parser.parse_args()


def init_cmd(args):
    cmd = "cd %(dir)s && tox -e %(env)s" % {"dir": args.directory,
                                            "env": args.env}
    if args.testr:
        return " ".join([cmd, args.testr])
    return cmd


def main():
    args = process_args()
    LOG.info("Processed args: %(args)s" % {"args": args})
    ssh = sshutils.SSH(host=args.ip_address,
                       user=args.username,
                       password=args.password)
    ssh._get_client()
    cmd = init_cmd(args)
    LOG.info('Command to execute: %(cmd)s' % {"cmd": cmd})
    ssh.run(cmd)

if __name__ == '__main__':
    main()