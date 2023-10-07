#!/usr/bin/env python

import argparse
import os
import re
import subprocess


def get_pid(node_name):
    """Get the system process ID for the node.

    """
    node_pat = re.compile('.*bash .* mininet:{}'.format(node_name))

    lines = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE).stdout.readlines()
    for line in lines:
        line_string = str(line)
        match = node_pat.match(line_string)
        if not match:
            continue
        pid = line_string.split()[1]
        return pid

    raise KeyError("No process found for {}".format(node_name))


def main():
    """Entry point for attach.

    """
    parser = argparse.ArgumentParser("Connect to a mininet node.")
    parser.add_argument('-n', '--node',
                        required=True,
                        help="The node's name (e.g., h1_1, R1, etc.)")
    parser.add_argument('-d', '--daemon',
                        help="Connect directly to this FRR daemon.")
    parser.add_argument('-c', '--cmd',
                        default=["sh"],
                        nargs="+",
                        help="Command to run on the node."
                        " Default is to start sh.")
    args = parser.parse_args()

    pid = get_pid(args.node)
    cmd = ' '.join(args.cmd)
    if args.daemon is not None:
        port_dict = {
            "zebrasrv": 2600,
            "zebra": 2601,
            "ripd": 2602,
            "ripngd": 2603,
            "ospfd": 2604,
            "bgpd": 2605,
            "ospf6d": 2606,
            "ospfapi": 2607,
            "isisd": 2608,
            "staticd": 2616,
        }

        cmd = "telnet localhost {}".format(port_dict[args.daemon])

    os.system("mnexec -a {} {}".format(pid, cmd))


if __name__ == '__main__':
    main()
