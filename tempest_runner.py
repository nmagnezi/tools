#!/usr/bin/env python

import argparse
import logging
import subprocess


LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
console = logging.StreamHandler()
LOG.addHandler(console)


TESTENV = 'all'
TEMPEST_DIRECTORY = "/opt/openstack/tempest"


def process_args():
    parser = argparse.ArgumentParser(description='Tempest runner for Devstack')

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
    cmd = ("tox -c %(directory)s/tox.ini -e %(env)s"
           % {"env": args.env, "directory": args.directory})
    if args.testr:
        return " ".join([cmd, args.testr])
    return cmd


def main():
    args = process_args()
    LOG.info("Processed args: %(args)s" % {"args": args})
    cmd = init_cmd(args)
    LOG.info('Command to execute: %(cmd)s' % {"cmd": cmd})
    subprocess.check_call(['cd', args.directory])
    subprocess.check_call(cmd.split())

if __name__ == '__main__':
    main()