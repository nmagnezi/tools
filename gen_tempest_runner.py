#!/usr/bin/env python

import argparse

TESTENV = 'all'
TEMPEST_DIRECTORY = "/opt/openstack/tempest"
RESULTS_XML = "xunit"
TEMPEST_LOG = "tempest.log"


def process_args():
    parser = argparse.ArgumentParser(description='Tempest runner for Devstack')

    parser.add_argument('-t', '--tests',
                        help='wildcard for tests to run', required=False)
    parser.add_argument('-d', '--directory',
                        help='Tempest directory', required=False,
                        default=TEMPEST_DIRECTORY)

    return parser.parse_args()


def init_cmd(args):
    cmd = list()
    cmd.append("testr run")
    if args.tests:
        cmd.append(args.tests)
    cmd.append("--subunit | tee >(subunit2junitxml "
               "--output-to=%(directory)s/%(results)s.xml) "
               "| subunit-2to1 | tee %(directory)s/%(log)s "
               "| %(directory)s/tools/colorizer.py"
               % {"results": RESULTS_XML,
                  "log": TEMPEST_LOG,
                  "directory": args.directory})
    print "Generated Command: %(cmd)s" % {"cmd": cmd}
    return " ".join(cmd)


def generate_runner_script(cmd, args):
    lines = list()
    lines.append("#!/bin/bash\n")
    lines.append("python %(directory)s/tools/install_venv.py "
                 "--no-site-packages\n" % {"directory": args.directory})
    lines.append("source %(directory)s/.venv/bin/activate\n"
                 % {"directory": args.directory})
    lines.append("find . -type f -name '*.pyc' -delete\n")
    lines.append("pip install junitxml\n")
    lines.append("testr init\n")
    lines.append("echo > %(directory)s/%(log)s\n"
                 % {"directory": args.directory, "log": TEMPEST_LOG})
    lines.append("".join([cmd, "\n"]))

    with open("tempest.sh", 'w') as fo:
        for line in lines:
            fo.write(line)

def main():
    args = process_args()
    cmd = init_cmd(args)
    generate_runner_script(cmd, args)

if __name__ == '__main__':
    main()