#!/usr/bin/env python

import argparse

TESTENV = 'all'
TEMPEST_DIRECTORY = "/opt/openstack/tempest"
RESULTS_XML = "nosetests"
TEMPEST_LOG = "tempest.log"


class Exp(Exception):
    pass


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
    cmd = list()
    cmd.append("tox -c %(directory)s/tox.ini -e %(env)s -- --subunit"
               % {"env": args.env, "directory": args.directory})
    if args.testr:
        cmd.append(args.testr)
    cmd.append("| tee >( subunit2junitxml --output-to=%(results)s.xml ) "
               "| subunit-2to1 | tee %(directory)s/%(log)s "
               "| %(directory)s/tools/colorizer.py"
               % {"results": RESULTS_XML,
                  "log": TEMPEST_LOG,
                  "directory": args.directory})
    return " ".join(cmd)


def main():
    args = process_args()
    cmd = init_cmd(args)
    print '%(cmd)s' % {"cmd": cmd}

if __name__ == '__main__':
    main()